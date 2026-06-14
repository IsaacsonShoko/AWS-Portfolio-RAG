import type { Citation } from "@/lib/types";
import { Citations } from "./Citations";
import { Badge } from "@/components/ui/badge";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  followUps?: string[];
}

export function MessageBubble({ message, onFollowUpPick }: { message: ChatMessage; onFollowUpPick?: (q: string) => void }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[85%] rounded-md px-3 py-2 text-sm ${
          isUser ? "bg-[hsl(38,92%,55%)] text-[hsl(224,71%,4%)]" : "bg-muted text-foreground"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.text}</p>
        {!isUser && message.citations && <Citations citations={message.citations} />}
      </div>
      {!isUser && message.followUps && message.followUps.length > 0 && (
        <div className="flex flex-wrap gap-2 px-1">
          {message.followUps.map((q) => (
            <button key={q} type="button" onClick={() => onFollowUpPick?.(q)}>
              <Badge variant="outline" className="cursor-pointer hover:border-[hsl(38,92%,55%)]/50">
                {q}
              </Badge>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
