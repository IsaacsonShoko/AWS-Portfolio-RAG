import type { Citation } from "@/lib/types";
import { Citations } from "./Citations";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  followUps?: string[];
}

export function MessageBubble({ message, onFollowUpPick }: { message: ChatMessage; onFollowUpPick?: (q: string) => void }) {
  const isUser = message.role === "user";
  
  let processedText = message.text;
  if (!isUser) {
    // 1. Fix citations injected inside list numbers: "3[1]." -> "3. [1]"
    processedText = processedText.replace(/(\d+)\[(\d+)\]\./g, "$1. [$2]");
    // 2. Add newlines before list numbers if they follow a space or citation, ensuring lists render correctly
    processedText = processedText.replace(/(\s|\[\d+\])\s*(\d+\.\s+)/g, "$1\n\n$2");
    // 3. Ensure space between citation and bold text: "[2]**" -> "[2] **"
    processedText = processedText.replace(/(\[\d+\])(\*\*)/g, "$1 $2");
  }

  return (
    <div className={`flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[85%] rounded-md px-3 py-2 text-sm ${
          isUser ? "bg-[hsl(38,92%,55%)] text-[hsl(224,71%,4%)]" : "bg-muted text-foreground"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{processedText}</p>
        ) : (
          <div className="prose prose-sm prose-invert max-w-none break-words leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 ml-4 list-disc space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 ml-4 list-decimal space-y-1">{children}</ol>,
                li: ({ children }) => <li>{children}</li>,
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-[hsl(38,92%,55%)] hover:underline">
                    {children}
                  </a>
                ),
                strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
              }}
            >
              {processedText}
            </ReactMarkdown>
          </div>
        )}
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
