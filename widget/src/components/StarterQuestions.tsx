import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const STARTERS = [
  "What frameworks did he use for API calls?",
  "How did he handle authentication?",
  "Which projects use AWS?",
  "How is testing or deployment done?",
  "Why did he choose one tool over another?",
  "What is his biggest project?",
];

export function StarterQuestions({
  onPick, repos, repo, onRepoChange,
}: {
  onPick: (q: string) => void;
  repos: string[];
  repo: string | null;
  onRepoChange: (r: string | null) => void;
}) {
  return (
    <div className="space-y-3 p-3">
      {repos.length > 0 && (
        <Select value={repo ?? "all"} onValueChange={(val) => onRepoChange(val === "all" ? null : val)}>
          <SelectTrigger aria-label="Scope answers to one project">
            <SelectValue placeholder="All projects" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All projects</SelectItem>
            {repos.map((r) => (
              <SelectItem key={r} value={r}>
                {r}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      <div className="flex flex-wrap gap-2">
        {STARTERS.map((q) => (
          <button key={q} type="button" onClick={() => onPick(q)}>
            <Badge>{q}</Badge>
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
        <a
          href={import.meta.env.VITE_CONTACT_URL as string}
          target="_blank" rel="noopener noreferrer"
          className="text-[hsl(38,92%,55%)] hover:text-[hsl(38,92%,65%)]"
        >
          Prefer to talk to a human? Get in touch →
        </a>
        <a
          href={import.meta.env.VITE_LINKEDIN_URL as string}
          target="_blank" rel="noopener noreferrer"
          className="text-[hsl(38,92%,55%)] hover:text-[hsl(38,92%,65%)]"
        >
          LinkedIn →
        </a>
      </div>
    </div>
  );
}
