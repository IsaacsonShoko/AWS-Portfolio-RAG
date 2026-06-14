import { useState } from "react";
import { Github, ChevronDown } from "lucide-react";
import type { Citation } from "@/lib/types";

export function Citations({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState<number | null>(null);
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 border-t border-border/30 pt-2">
      <p className="mb-1 text-xs font-semibold text-muted-foreground">Sources</p>
      <ul className="space-y-1">
        {citations.map((c) => (
          <li key={c.id} className="text-sm">
            <div className="flex items-center gap-2">
              <span className="text-[hsl(38,92%,55%)]">[{c.id}]</span>
              <a
                href={c.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[hsl(38,92%,55%)] hover:text-[hsl(38,92%,65%)] underline-offset-2 hover:underline"
              >
                <Github className="h-3.5 w-3.5" />
                {c.path ?? c.github_url}
              </a>
              <button
                type="button"
                aria-label={`Toggle evidence for source ${c.id}`}
                onClick={() => setOpen(open === c.id ? null : c.id)}
                className="ml-auto inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                evidence <ChevronDown className={`h-3 w-3 transition-transform ${open === c.id ? "rotate-180" : ""}`} />
              </button>
            </div>
            {open === c.id && (
              <pre className="no-scrollbar mt-1 overflow-x-auto rounded-sm bg-secondary/60 p-2 text-xs text-secondary-foreground">
                {c.snippet}
              </pre>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
