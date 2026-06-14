# 4D Assistant — RAG Chatbot

A recruiter-facing chat widget that answers questions about an engineer's public GitHub
projects, grounded entirely in those repositories. The retrieval-augmented-generation (RAG)
pipeline is **purely AWS Bedrock**: documents are embedded with **Amazon Titan Text
Embeddings V2** into an **Amazon S3 Vectors** index (no OpenSearch Serverless), and answers
are generated with **Amazon Nova Lite** via Bedrock `RetrieveAndGenerate`. Every retrieved
chunk carries a `github_url`, so each answer is returned with numbered, clickable GitHub
citations. The front end is a self-contained **React 18 + Vite + TypeScript + Tailwind +
shadcn/ui** widget (`FourDAssistant`) that talks to the backend over a single HTTPS endpoint.

---

## Architecture

```
GitHub repos
   │  (GitHub Action: filter repos, write <file>.metadata.json sidecars with github_url)
   ▼
S3 data bucket  s3://<KB_S3_BUCKET>/repos/<repo>/...
   │
   ▼
Bedrock Knowledge Base
   ├─ Titan Text Embeddings V2 (1024-dim)
   └─ Amazon S3 Vectors index (cosine)        ← ingestion job embeds repos/*
   │
   ▼
Lambda  +  HTTP API Gateway  (POST /chat)
   ├─ Bedrock RetrieveAndGenerate (model: Amazon Nova Lite)
   ├─ Bedrock Guardrail (prompt-attack, PII, contextual grounding)
   └─ maps each chunk's github_url → numbered citations
   │  returns { answer, citations[], sessionId }
   ▼
FourDAssistant widget  (VITE_CHAT_API_URL)
   themed floating chat panel with clickable GitHub citations
```

**Streaming note:** V1 returns a **buffered** (non-streaming) JSON response, because neither
REST nor HTTP API Gateway supports true response streaming; the widget shows a typing
indicator while it waits. The documented streaming upgrade is a **Lambda Function URL**
(`InvokeMode = RESPONSE_STREAM`) calling `RetrieveAndGenerateStream`, which bypasses API
Gateway by design. You pick the endpoint at deploy time via `VITE_CHAT_API_URL`.

---

## Repository layout

```
AWS Portfolio RAG/
  blueprint.txt                         spec
  config.env.example                    shared infra/backend identifiers (copy to config.env)
  README.md
  scripts/
    prepare_repo_for_s3.py              filters repos, writes *.metadata.json sidecars
  .github/workflows/
    sync-repos-to-s3.yml                syncs repos -> S3; optional trigger-ingestion job
  infra/
    docs/console-walkthrough.md         click-by-click Console steps (maintained by hand)
    create_s3_vectors.py                S3 Vectors bucket + cosine index
    create_knowledge_base.py            Bedrock KB + S3 data source
    start_ingestion.py                  start + poll an ingestion job
    verify_retrieve.py                  retrieval smoke test (checks github_url metadata)
    create_guardrail.py                 Bedrock Guardrail
  backend/
    handler.py                          Lambda entry (API Gateway proxy, CORS, validation)
    bedrock.py                          RetrieveAndGenerate wrapper (grounding prompt, repo filter)
    citations.py                        pure function: response -> {answer, citations, sessionId}
    deploy.py                           zip + create/update Lambda
    requirements.txt
    tests/                              pytest (7 tests)
  widget/
    src/components/FourDAssistant.tsx   top-level widget (+ Launcher, ChatPanel, etc.)
    src/lib/                            api.ts, types.ts, utils.ts
    src/index.css                       theme tokens + .fourd-assistant scoped utilities
    src/main.tsx                        standalone dev page entry
    src/embed.tsx                       embeddable entry: mountFourDAssistant('#id')
    test/                               vitest (8 tests)
    .env.example
  docs/                                 plan and design notes
```

---

## Local widget development

```bash
cd widget
cp .env.example .env        # then set VITE_CHAT_API_URL to your deployed POST /chat URL
npm install
npm run dev                 # standalone dev page at the Vite URL
```

Other widget scripts:

```bash
npm test                    # vitest run (8 tests)
npm run build               # type-check + production build -> dist/
npm run build:embed         # embeddable bundle -> dist/fourd-assistant.umd.cjs (+ .js, style.css)
```

> `build` and `build:embed` both run `vite build`, which is configured as a library build
> (`src/embed.tsx`) emitting `dist/fourd-assistant.umd.cjs`, `dist/fourd-assistant.js`, and
> `dist/style.css`. `build` additionally runs `tsc -b` first.

---

## Environment variables

### Widget (`widget/.env`)

| Variable             | Required | Description                                              |
| -------------------- | -------- | -------------------------------------------------------- |
| `VITE_CHAT_API_URL`  | yes      | Backend chat endpoint (API Gateway `POST /chat` URL, or Lambda Function URL if streaming). |
| `VITE_CONTACT_URL`   | no       | Contact CTA link shown in the panel.                     |
| `VITE_LINKEDIN_URL`  | no       | LinkedIn link shown in the panel.                        |

### Lambda (function environment)

| Variable             | Required | Description                                              |
| -------------------- | -------- | -------------------------------------------------------- |
| `KB_ID`              | yes      | Bedrock Knowledge Base ID.                               |
| `GEN_MODEL_ARN`      | yes      | Nova Lite generation model ARN (cross-region inference profile, e.g. `us.amazon.nova-lite-v1:0`). |
| `GUARDRAIL_ID`       | no       | Bedrock Guardrail ID; omit to run without a guardrail.   |
| `GUARDRAIL_VERSION`  | no       | Guardrail version (default `DRAFT`).                     |
| `NUM_RESULTS`        | no       | Retrieved chunks per query (default `6`).                |

> `AWS_REGION` is provided automatically by the Lambda runtime and is never set explicitly.
> The full set of provisioning identifiers used by the `infra/` and `backend/deploy.py`
> scripts (region, account, buckets, vector index, embedding model, KB/data-source/guardrail
> IDs, role ARNs) lives in **`config.env.example`** — copy it to `config.env` (git-ignored)
> and fill it in as you create resources.

---

## Required IAM (least privilege)

Three roles, each scoped to only what it uses. The GitHub Action authenticates via **OIDC**
(no long-lived secrets).

### 1. GitHub OIDC role (used by the GitHub Action)

- `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` on the data bucket and `repos/*`
  (`arn:aws:s3:::<KB_S3_BUCKET>` and `arn:aws:s3:::<KB_S3_BUCKET>/repos/*`).
- `bedrock:StartIngestionJob` on the KB — only needed if you enable the optional
  `trigger-ingestion` job in the workflow.

### 2. Bedrock Knowledge Base service role (`KB_ROLE_ARN`)

- `bedrock:InvokeModel` on the Titan embedding model
  (`amazon.titan-embed-text-v2:0`).
- `s3:GetObject`, `s3:ListBucket` on the data bucket
  (`arn:aws:s3:::<KB_S3_BUCKET>` and `.../repos/*`).
- S3 Vectors put/query/get (e.g. `s3vectors:PutVectors`, `s3vectors:QueryVectors`,
  `s3vectors:GetVectors`) on the vector bucket and index ARNs.

### 3. Lambda execution role (`LAMBDA_ROLE_ARN`)

- `AWSLambdaBasicExecutionRole` (CloudWatch Logs).
- `bedrock:RetrieveAndGenerate`, `bedrock:Retrieve` on the Knowledge Base ARN.
- `bedrock:InvokeModel` on the Nova Lite model ARN.
- `bedrock:ApplyGuardrail` on the Guardrail ARN.

---

## Provision / rebuild order

All `infra/` and `backend/` scripts read identifiers from `config.env`, so `source config.env`
first.

1. **Config** — copy and fill the template:
   `cp config.env.example config.env` and populate values as you create resources.
2. **Data bucket + sync** — create the S3 data bucket, then run the GitHub Action
   (Actions → *Sync portfolio repos to S3* → Run workflow) to populate
   `s3://<KB_S3_BUCKET>/repos/`.
3. **Vector store** — `python infra/create_s3_vectors.py`
   (creates the S3 Vectors bucket + cosine index, dim 1024).
4. **Knowledge Base** — create the KB in the Console per
   `infra/docs/console-walkthrough.md`, or `python infra/create_knowledge_base.py`; paste the
   printed `KB_ID` and `DATA_SOURCE_ID` into `config.env`.
5. **Ingestion** — `python infra/start_ingestion.py` (starts and polls a job to COMPLETE).
6. **Verify retrieval** — `python infra/verify_retrieve.py "How did he handle authentication?"`;
   confirm results carry real `github_url`s.
7. **Guardrail** — `python infra/create_guardrail.py`; paste the printed `GUARDRAIL_ID` into
   `config.env`.
8. **Deploy Lambda** — `python backend/deploy.py` (zips `backend/`, creates/updates the
   `fourd-chat` function with the Lambda env vars above).
9. **API Gateway** — wire an HTTP API `POST /chat` route to the Lambda (with CORS), then set
   the widget's `VITE_CHAT_API_URL` to the invoke URL.

---

## Running an ingestion after a repo sync

When repository content changes:

1. Trigger the GitHub Action (Actions tab → *Sync portfolio repos to S3* → Run workflow).
   The sync uses `--size-only`, so unchanged files are not re-uploaded (and not re-embedded).
2. Start a fresh ingestion job: `source config.env && python infra/start_ingestion.py`.

Alternatively, set the repository variables `BEDROCK_KB_ID` and `BEDROCK_DATA_SOURCE_ID`
(and `AWS_REGION` / `AWS_ROLE_ARN`) and the workflow's optional `trigger-ingestion` job will
start the ingestion automatically after each sync.

---

## Embedding into the 4D Analytics site

The widget is fully scoped: everything renders inside a `.fourd-assistant` wrapper, and the
theme tokens — defined on `:root` in `widget/src/index.css` — are consumed only through that
class, so nothing leaks into the host page. Render it **once**.

**Option A — source integration (recommended).**
Copy `widget/src/components/*` and `widget/src/lib/*` into the site, and copy the `:root`
token block from `widget/src/index.css` into the site's global stylesheet. Then render the
component once inside the site `Layout`:

```tsx
import { FourDAssistant } from "@/components/FourDAssistant";

<FourDAssistant />   // optionally: <FourDAssistant repos={["repo-a", "repo-b"]} />
```

No router or global-style changes are required.

**Option B — prebuilt bundle.**
Build the embeddable bundle (`cd widget && npm run build:embed`) and load
`dist/fourd-assistant.umd.cjs` plus `dist/style.css` on the host page, then mount it:

```html
<div id="fourd-assistant"></div>
<link rel="stylesheet" href="/path/to/style.css" />
<script src="/path/to/fourd-assistant.umd.cjs"></script>
<script>FourDAssistant.mountFourDAssistant('#fourd-assistant');</script>
```

A `#fourd-assistant` container also auto-mounts on load.

---

## Testing

```bash
# Backend (from repo root)
python -m pytest backend/ -v          # 7 tests

# Widget
cd widget && npm test                 # 8 tests (vitest)
```

---

## Cost & scope notes

- **Cost:** the S3 sync is `--size-only`, so unchanged files are never re-uploaded or
  re-embedded; generation uses low-cost **Nova Lite**; the Lambda caps input at **1000
  characters** per message.
- **V1 scope excludes:** Bedrock Agents / tool-use, multi-user accounts, and any write paths.
- **Deferred (with reason, not silent gaps):**
  - *True token streaming* — API Gateway cannot stream; documented as a Lambda Function URL
    upgrade.
  - *Hard relevance-score cutoff* — covered for V1 by the grounding prompt + Guardrail
    contextual-grounding filter + dropping references without a `github_url`.
  - *API rate limiting* — add an API Gateway usage plan / throttle if needed.
