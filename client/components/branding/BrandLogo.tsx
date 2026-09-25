import { cn } from "@/lib/format";

/**
 * A program's logo, or the stock Loyalty Engine mark when it has none.
 *
 * Height comes from `className`; width follows the image, so a wide wordmark
 * keeps its shape instead of being squeezed into a square. Callers cap it with
 * a `max-w-*`.
 */
export function BrandLogo({
  src,
  alt,
  className,
}: {
  src: string | null | undefined;
  alt: string;
  className?: string;
}) {
  return (
    // A plain <img>, not next/image: the logo lives in Supabase Storage at any
    // aspect ratio, often as an SVG, so there is nothing for the optimizer to
    // do and no fixed width/height to declare.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src || "/logo.svg"}
      alt={alt}
      className={cn("w-auto shrink-0 object-contain", className)}
    />
  );
}
