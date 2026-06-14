import type { Citation } from "@/lib/types";
import { Citations } from "./Citations";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-md px-3 py-2 text-sm ${
          isUser ? "bg-[hsl(38,92%,55%)] text-[hsl(224,71%,4%)]" : "bg-muted text-foreground"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.text}</p>
        {!isUser && message.citations && <Citations citations={message.citations} />}
      </div>
    </div>
  );
}
