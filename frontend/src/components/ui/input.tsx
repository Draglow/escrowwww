import * as React from "react"
import { cn } from "@/lib/utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          // Base
          "flex h-11 w-full rounded-lg border border-input bg-background px-4 py-2.5 text-sm",
          "ring-offset-background",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium",
          "placeholder:text-muted-foreground/60",
          // 3D inset depth
          "shadow-[inset_0_2px_4px_rgba(0,0,0,0.07),inset_0_1px_2px_rgba(0,0,0,0.05),0_1px_0_rgba(255,255,255,0.8)]",
          "dark:shadow-[inset_0_2px_4px_rgba(0,0,0,0.25),inset_0_1px_2px_rgba(0,0,0,0.2)]",
          // Focus ring
          "focus-visible:outline-none",
          "focus-visible:border-primary/60",
          "focus-visible:shadow-[inset_0_2px_4px_rgba(0,0,0,0.05),0_0_0_3px_hsl(var(--ring)/0.18),0_1px_0_rgba(255,255,255,0.8)]",
          "dark:focus-visible:shadow-[inset_0_2px_4px_rgba(0,0,0,0.2),0_0_0_3px_hsl(var(--ring)/0.25)]",
          "transition-[box-shadow,border-color] duration-200",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
