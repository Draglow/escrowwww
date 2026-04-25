import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  [
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold",
    "transition-[box-shadow,transform] duration-200",
    "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    // 3D depth
    "shadow-[0_1px_3px_rgba(0,0,0,0.12),inset_0_1px_0_rgba(255,255,255,0.18)]",
  ].join(" "),
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/85 hover:shadow-[0_2px_6px_hsl(var(--primary)/0.35),inset_0_1px_0_rgba(255,255,255,0.22)]",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/85 hover:shadow-[0_2px_6px_hsl(var(--destructive)/0.3)]",
        outline:
          "text-foreground border-border/60 hover:border-primary/40 hover:bg-accent",
        success:
          "border-transparent bg-green-500/15 text-green-600 dark:text-green-400 border-green-500/20 hover:bg-green-500/20",
        warning:
          "border-transparent bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/20 hover:bg-yellow-500/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
