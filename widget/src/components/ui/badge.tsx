import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-border/50 bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground hover:border-[hsl(38,92%,55%)]/50 transition-colors",
        className,
      )}
      {...props}
    />
  );
}
