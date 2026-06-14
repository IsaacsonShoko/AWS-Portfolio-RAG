import { useState } from "react";
import { Toaster, toast } from "sonner";
import { Launcher } from "./Launcher";
import { ChatPanel } from "./ChatPanel";
import type { ChatMessage } from "./MessageBubble";
import { sendChat } from "@/lib/api";

export interface FourDAssistantProps {
  /** Optional list of repo names to populate the project filter. */
  repos?: string[];
}

export function FourDAssistant({ repos = [] }: FourDAssistantProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [repo, setRepo] = useState<string | null>(null);

  async function handleSend(text: string) {
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const res = await sendChat({ message: text, sessionId, repo: repo ?? undefined });
      setSessionId(res.sessionId);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, citations: res.citations, followUps: res.followUps }]);
    } catch {
      toast.error("The assistant is temporarily unavailable. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fourd-assistant">
      <Toaster theme="dark" position="bottom-right" />
      {open ? (
        <ChatPanel
          messages={messages}
          loading={loading}
          repos={repos}
          repo={repo}
          onRepoChange={setRepo}
          onSend={handleSend}
          onClose={() => setOpen(false)}
        />
      ) : (
        <Launcher onClick={() => setOpen(true)} />
      )}
    </div>
  );
}
