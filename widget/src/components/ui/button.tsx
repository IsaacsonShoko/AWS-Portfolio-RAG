import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50",
  {
    variants: {
      variant: {
        // Primary CTA: rounded-none, amber fill, near-black text, darker amber hover.
        default: "rounded-none bg-[hsl(38,92%,55%)] text-[hsl(224,71%,4%)] hover:bg-[hsl(38,92%,45%)]",
        outline: "rounded-none border border-border bg-transparent hover:border-[hsl(38,92%,55%)]/50",
        ghost: "rounded-md hover:bg-secondary",
      },
      size: { default: "h-9 px-4", sm: "h-8 px-3", icon: "h-12 w-12 rounded-full" },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";
export { buttonVariants };
