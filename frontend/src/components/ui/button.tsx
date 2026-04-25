import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  // Base — shared across all variants
  [
    "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-semibold",
    "ring-offset-background",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-50",
    // Smooth press animation
    "transition-[box-shadow,transform,background-color,opacity] duration-200 ease-out",
    "active:scale-[0.97]",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-primary text-primary-foreground",
          // 3D bottom-edge shadow + specular top highlight
          "shadow-[0_4px_0_hsl(var(--primary)/0.45),0_6px_16px_hsl(var(--primary)/0.25),inset_0_1px_0_rgba(255,255,255,0.22)]",
          "hover:bg-primary/95",
          "hover:shadow-[0_6px_0_hsl(var(--primary)/0.4),0_10px_24px_hsl(var(--primary)/0.3),inset_0_1px_0_rgba(255,255,255,0.28)]",
          "hover:-translate-y-0.5",
          "active:shadow-[0_1px_0_hsl(var(--primary)/0.4),0_2px_6px_hsl(var(--primary)/0.2),inset_0_2px_4px_rgba(0,0,0,0.12)]",
          "active:translate-y-0.5",
        ].join(" "),

        destructive: [
          "bg-destructive text-destructive-foreground",
          "shadow-[0_4px_0_hsl(var(--destructive)/0.45),0_6px_16px_hsl(var(--destructive)/0.2),inset_0_1px_0_rgba(255,255,255,0.18)]",
          "hover:bg-destructive/95 hover:-translate-y-0.5",
          "hover:shadow-[0_6px_0_hsl(var(--destructive)/0.4),0_10px_24px_hsl(var(--destructive)/0.25)]",
          "active:shadow-[0_1px_0_hsl(var(--destructive)/0.4)] active:translate-y-0.5",
        ].join(" "),

        outline: [
          "border-2 border-input bg-background",
          "shadow-[0_2px_4px_rgba(0,0,0,0.06),0_1px_2px_rgba(0,0,0,0.04),inset_0_1px_0_rgba(255,255,255,0.8)]",
          "hover:bg-accent hover:text-accent-foreground hover:border-primary/40 hover:-translate-y-0.5",
          "hover:shadow-[0_4px_8px_rgba(0,0,0,0.1),0_2px_4px_rgba(0,0,0,0.06)]",
          "active:shadow-[inset_0_2px_4px_rgba(0,0,0,0.08)] active:translate-y-0",
        ].join(" "),

        secondary: [
          "bg-secondary text-secondary-foreground",
          "shadow-[0_2px_4px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.7)]",
          "hover:bg-secondary/80 hover:-translate-y-0.5",
          "hover:shadow-[0_4px_8px_rgba(0,0,0,0.1)]",
          "active:shadow-[inset_0_2px_4px_rgba(0,0,0,0.08)] active:translate-y-0",
        ].join(" "),

        ghost: [
          "hover:bg-accent hover:text-accent-foreground",
          "hover:shadow-[0_2px_8px_rgba(0,0,0,0.06)]",
        ].join(" "),

        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-12 rounded-xl px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
