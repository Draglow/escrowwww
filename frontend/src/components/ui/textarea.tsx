import * as React from "react"
import { cn } from "@/lib/utils"

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          // Base
          "flex min-h-[88px] w-full rounded-lg border border-input bg-background px-4 py-3 text-sm",
          "ring-offset-background",
          "placeholder:text-muted-foreground/60",
          // 3D inset depth
          "shadow-[inset_0_2px_4px_rgba(0,0,0,0.07),inset_0_1px_2px_rgba(0,0,0,0.05),0_1px_0_rgba(255,255,255,0.8)]",
          "dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.25),inset_0_1px_2px_rgba(0,0,0,0.2)]",
          // Focus
          "focus-visible:outline-none",
          "focus-visible:border-primary/60",
          "focus-visible:shadow-[inset_0_2px_4px_rgba(0,0,0,0.05),0_0_0_3px_hsl(var(--ring)/0.18),0_1px_0_rgba(255,255,255,0.8)]",
          "dark:focus-visible:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2),0_0_0_3px_hsl(var(--ring)/0.25)]",
          "transition-[box-shadow,border-color] duration-200",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "resize-none",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea }
