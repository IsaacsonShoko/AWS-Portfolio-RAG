import { motion } from "framer-motion";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Launcher({ onClick }: { onClick: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-6 right-6 z-[60]">
      <Button
        size="icon"
        aria-label="Open the 4D portfolio assistant"
        onClick={onClick}
        className="glass glow-accent relative bg-[hsl(38,92%,55%)] text-[hsl(224,71%,4%)] hover:bg-[hsl(38,92%,45%)]"
      >
        <MessageCircle className="h-5 w-5" />
        <span className="absolute right-2 top-2 h-2 w-2 animate-pulse rounded-full bg-[hsl(38,92%,55%)]" />
      </Button>
    </motion.div>
  );
}
