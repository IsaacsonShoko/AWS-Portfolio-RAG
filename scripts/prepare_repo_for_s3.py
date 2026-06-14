#!/usr/bin/env python3
"""
Prepare a checked-out git repository for upload to S3 as an Amazon Bedrock
Knowledge Base data source.

Goal: keep only the files that help answer questions about the project
(source, documentation, and stack revealing config) and drop the noise that
would otherwise inflate embedding cost: lockfiles, build output, binaries,
media, datasets, minified bundles, caches, and secrets.

For every kept file it also writes a "<file>.metadata.json" sidecar carrying
owner, repo, branch, language, path, and a prebuilt github_url, so Bedrock can
filter retrieval and the bot can cite each source as a clickable GitHub link.

Usage:
    python prepare_repo_for_s3.py --src _repo --out _clean \
        --owner my-username --repo my-repo --branch main \
        --max-bytes 204800 --summary _summary.md
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from urllib.parse import quote

# Directories that never carry useful, embeddable signal.
EXCLUDED_DIRS = {
    ".git", ".github", ".gitlab", ".circleci",
    "node_modules", "bower_components", "vendor", "venv", ".venv", "env",
    "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", "target",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".cache", ".turbo", ".parcel-cache", ".gradle",
    "coverage", "htmlcov", ".idea", ".vscode",
    "tmp", "temp", "logs", ".terraform",
}

# Exact file names that are noise even when the extension is allowed.
EXCLUDED_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json",
    "poetry.lock", "Pipfile.lock", "composer.lock", "Cargo.lock",
    "go.sum", "Gemfile.lock", "flake.lock",
}

# Suffixes that are generated or non textual even with an allowed extension.
EXCLUDED_SUFFIXES = (".min.js", ".min.css", ".map", ".lock", ".snap")

# Secret bearing files are never uploaded.
SECRET_SUFFIXES = (".pem", ".key", ".pfx", ".crt", ".p12", ".pkcs12")

# Allowlist of extensions worth embedding.
ALLOWED_EXTENSIONS = {
    # docs
    ".md", ".mdx", ".markdown", ".rst", ".adoc", ".txt",
    # python (notebooks .ipynb excluded on purpose, they are heavy json)
    ".py", ".pyi",
    # javascript / typescript / web frameworks
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro",
    # jvm / systems / other languages
    ".java", ".kt", ".kts", ".go", ".rs", ".rb", ".php",
    ".cs", ".c", ".h", ".cpp", ".hpp", ".cc",
    ".swift", ".scala", ".dart", ".lua", ".r",
    # shell / infrastructure as code
    ".sh", ".bash", ".zsh", ".ps1", ".tf", ".tfvars", ".bicep",
    # stack revealing config and schemas
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".gradle", ".proto", ".graphql", ".gql", ".prisma", ".sql",
    ".html", ".css", ".scss",
}

# Extensionless or specially named files worth keeping.
ALLOWED_FILENAMES = {
    "Dockerfile", "Makefile", "Procfile", "Rakefile",
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "tsconfig.json", "go.mod", "Cargo.toml",
    "Pipfile", "Gemfile", "docker-compose.yml", "docker-compose.yaml",
}

LANGUAGE_BY_EXT = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".vue": "vue", ".svelte": "svelte", ".astro": "astro",
    ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
    ".cs": "csharp", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp",
    ".swift": "swift", ".scala": "scala", ".dart": "dart", ".lua": "lua", ".r": "r",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".ps1": "powershell",
    ".tf": "terraform", ".tfvars": "terraform", ".bicep": "bicep",
    ".sql": "sql", ".proto": "protobuf", ".graphql": "graphql", ".gql": "graphql",
    ".prisma": "prisma",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".ini": "config", ".cfg": "config", ".gradle": "gradle",
    ".html": "html", ".css": "css", ".scss": "scss",
    ".md": "markdown", ".mdx": "markdown", ".markdown": "markdown",
    ".rst": "docs", ".adoc": "docs", ".txt": "text",
}


def language_for(path: Path) -> str:
    return LANGUAGE_BY_EXT.get(path.suffix.lower(), "other")


def is_probably_text(path: Path, sniff_bytes: int = 4096) -> bool:
    """Cheap binary check: reject null bytes and non utf-8 content."""
    try:
        with open(path, "rb") as handle:
            chunk = handle.read(sniff_bytes)
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def decide(path: Path, max_bytes: int) -> tuple[bool, str]:
    """Return (keep, reason)."""
    name = path.name
    lower = name.lower()

    if lower == ".env" or lower.startswith(".env"):
        return False, "secret"
    if path.suffix.lower() in SECRET_SUFFIXES:
        return False, "secret"
    if name in EXCLUDED_FILENAMES:
        return False, "lockfile"
    if any(lower.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return False, "generated"

    allowed = path.suffix.lower() in ALLOWED_EXTENSIONS or name in ALLOWED_FILENAMES
    if not allowed:
        return False, "not-allowlisted"

    try:
        size = path.stat().st_size
    except OSError:
        return False, "unreadable"
    if size == 0:
        return False, "empty"
    if size > max_bytes:
        return False, "too-large"
    if not is_probably_text(path):
        return False, "binary"

    return True, "kept"


def build_github_url(owner: str, repo: str, branch: str, rel_posix: str) -> str:
    # Encode each path segment so files with spaces or special characters still link.
    encoded_path = quote(rel_posix, safe="/")
    return f"https://github.com/{owner}/{repo}/blob/{branch}/{encoded_path}"


def write_sidecar(
    dest_file: Path,
    owner: str,
    repo: str,
    branch: str,
    rel_posix: str,
    language: str,
    github_url: str,
) -> None:
    sidecar = dest_file.with_name(dest_file.name + ".metadata.json")
    payload = {
        "metadataAttributes": {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "language": language,
            "path": rel_posix,
            "github_url": github_url,
        }
    }
    sidecar.write_text(json.dumps(payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, help="Checked out repo directory")
    parser.add_argument("--out", required=True, help="Output directory for the clean payload")
    parser.add_argument("--owner", required=True, help="GitHub owner or org, used for citation links")
    parser.add_argument("--repo", required=True, help="Repo name, used as a metadata tag and S3 prefix")
    parser.add_argument("--branch", default="main", help="Default branch, used to build the github_url")
    parser.add_argument("--max-bytes", type=int, default=200 * 1024, help="Skip files larger than this")
    parser.add_argument("--summary", default=None, help="Optional path to write a markdown summary")
    args = parser.parse_args()

    src_root = Path(args.src).resolve()
    out_root = Path(args.out).resolve()
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    reasons: Counter[str] = Counter()
    kept_files = 0
    kept_bytes = 0

    for current_dir, dir_names, file_names in os.walk(src_root):
        # Prune excluded directories in place so we never descend into them.
        dir_names[:] = [d for d in dir_names if d not in EXCLUDED_DIRS]

        for file_name in file_names:
            source = Path(current_dir) / file_name
            if source.is_symlink():
                reasons["symlink"] += 1
                continue

            keep, reason = decide(source, args.max_bytes)
            reasons[reason] += 1
            if not keep:
                continue

            rel = source.relative_to(src_root)
            rel_posix = rel.as_posix()
            dest = out_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            github_url = build_github_url(args.owner, args.repo, args.branch, rel_posix)
            write_sidecar(
                dest,
                args.owner,
                args.repo,
                args.branch,
                rel_posix,
                language_for(source),
                github_url,
            )

            kept_files += 1
            kept_bytes += source.stat().st_size

    skipped = sum(count for reason, count in reasons.items() if reason != "kept")

    lines = [
        "",
        f"Kept **{kept_files}** files ({kept_bytes / 1024:.1f} KB), skipped **{skipped}**.",
        "",
        "| Outcome | Files |",
        "| --- | --- |",
    ]
    for reason, count in sorted(reasons.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {reason} | {count} |")
    report = "\n".join(lines)

    print(report)
    if args.summary:
        Path(args.summary).write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
