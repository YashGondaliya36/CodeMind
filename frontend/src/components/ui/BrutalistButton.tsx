import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "acid" | "orange"
}

const BrutalistButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => {
    
    // Core brutalist styles: thick border, solid shadow, active state pushes down
    const baseStyles = "inline-flex items-center justify-center whitespace-nowrap px-6 py-3 font-bold border-3 border-brutal-black transition-all shadow-brutal hover:-translate-y-1 hover:shadow-brutal-lg active:translate-y-1 active:shadow-brutal-hover disabled:pointer-events-none disabled:opacity-50"
    
    const variants = {
      default: "bg-brutal-white text-brutal-black hover:bg-brutal-gray",
      acid: "bg-brutal-green text-brutal-black",
      orange: "bg-brutal-orange text-brutal-black",
    }

    return (
      <button
        className={cn(baseStyles, variants[variant], className)}
        ref={ref}
        {...props}
      />
    )
  }
)
BrutalistButton.displayName = "BrutalistButton"

export { BrutalistButton }
