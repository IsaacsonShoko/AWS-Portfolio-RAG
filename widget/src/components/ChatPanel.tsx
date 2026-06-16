import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { X, Send } from "lucide-react";
import { MessageList } from "./MessageList";
import { StarterQuestions } from "./StarterQuestions";
import type { ChatMessage } from "./MessageBubble";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function ChatPanel({
  messages, loading, repos, repo, onRepoChange, onSend, onClose,
}: {
  messages: ChatMessage[];
  loading: boolean;
  repos: string[];
  repo: string | null;
  onRepoChange: (r: string | null) => void;
  onSend: (text: string) => void;
  onClose: () => void;
}) {
  const [draft, setDraft] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    onSend(text);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      role="dialog" aria-label="4D portfolio assistant"
      className="panel dot-grid fixed bottom-6 right-6 z-[60] flex h-[32rem] w-[22rem] min-h-[24rem] min-w-[20rem] resize flex-col overflow-hidden rounded-lg sm:bottom-6 max-sm:inset-0 max-sm:h-full max-sm:w-full max-sm:rounded-none max-sm:resize-none"
    >
      <header className="flex flex-col border-b border-border/30 p-3">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-base">
            Ask about <span className="gradient-text">my work</span>
          </h2>
          <button aria-label="Close assistant" onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Powered by Github, AWS S3, AWS Knowledgebase, s3 Vectors, amazon titan and novalite
        </p>
      </header>

      {messages.length === 0 ? (
        <StarterQuestions onPick={onSend} repos={repos} repo={repo} onRepoChange={onRepoChange} />
      ) : (
        <MessageList messages={messages} loading={loading} onFollowUpPick={onSend} />
      )}

      <p className="px-3 pb-1 text-[10px] text-muted-foreground">
        AI assistant answering only from public GitHub repositories.
      </p>
      <form onSubmit={submit} className="flex gap-2 border-t border-border/30 p-3">
        <Input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a question…"
          aria-label="Ask a question"
          className="flex-1"
        />
        <Button type="submit" size="sm" aria-label="Send"><Send className="h-4 w-4" /></Button>
      </form>
    </motion.div>
  );
}
