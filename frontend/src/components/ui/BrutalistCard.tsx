import * as React from "react"
import { cn } from "@/lib/utils"

const BrutalistCard = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "border-3 border-brutal-black bg-brutal-white shadow-brutal",
      className
    )}
    {...props}
  />
))
BrutalistCard.displayName = "BrutalistCard"

const BrutalistCardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6 border-b-3 border-brutal-black bg-brutal-gray/20", className)}
    {...props}
  />
))
BrutalistCardHeader.displayName = "BrutalistCardHeader"

const BrutalistCardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-sans font-bold text-2xl tracking-tight uppercase", className)}
    {...props}
  />
))
BrutalistCardTitle.displayName = "BrutalistCardTitle"

const BrutalistCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
BrutalistCardContent.displayName = "BrutalistCardContent"

export { BrutalistCard, BrutalistCardHeader, BrutalistCardTitle, BrutalistCardContent }
