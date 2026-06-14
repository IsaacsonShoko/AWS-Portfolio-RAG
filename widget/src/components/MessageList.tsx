import { MessageBubble, type ChatMessage } from "./MessageBubble";

function TypingIndicator() {
  return (
    <div className="flex gap-1" aria-label="Assistant is typing">
      {[0, 1, 2].map((i) => (
        <span key={i} className="h-2 w-2 animate-pulse rounded-full bg-[hsl(38,92%,55%)]"
          style={{ animationDelay: `${i * 150}ms` }} />
      ))}
    </div>
  );
}

export function MessageList({ messages, loading, onFollowUpPick }: { messages: ChatMessage[]; loading: boolean; onFollowUpPick?: (q: string) => void }) {
  return (
    <div className="no-scrollbar flex-1 space-y-3 overflow-y-auto p-3">
      {messages.map((m, i) => <MessageBubble key={i} message={m} onFollowUpPick={onFollowUpPick} />)}
      {loading && <TypingIndicator />}
    </div>
  );
}
