import { cn } from "@/lib/format";

/**
 * Page loader built from the brand mark (public/logo.svg), drawn inline so its
 * parts can move: the tile floats over a ground shadow, the medallion flips like
 * a coin, the ribbon tails flutter and a glint sweeps the tile after each flip.
 * Keyframes live in globals.css (`loader-*`).
 *
 * It fades in after a short delay, so fast navigations never flash it.
 */
export function LogoLoader({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn("loader-enter flex flex-col items-center gap-3", className)}
    >
      <svg
        className="loader-float h-16 w-16"
        viewBox="0 0 40 40"
        fill="none"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="loader-bg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#6d5ef0" />
            <stop offset="1" stopColor="#4c3fbf" />
          </linearGradient>
          <linearGradient id="loader-hl" x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0.2" />
            <stop offset="0.55" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="loader-glint" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0" />
            <stop offset="0.5" stopColor="#ffffff" stopOpacity="0.45" />
            <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
          <clipPath id="loader-tile">
            <rect width="40" height="40" rx="11" />
          </clipPath>
        </defs>

        <rect width="40" height="40" rx="11" fill="url(#loader-bg)" />
        <rect width="40" height="40" rx="11" fill="url(#loader-hl)" />

        <path className="loader-ribbon-left" d="M15.5,14 L19,14 L19,33 L17.25,30.5 L15.5,33 Z" fill="#ffffff" />
        <path className="loader-ribbon-right" d="M21,14 L24.5,14 L24.5,33 L22.75,30.5 L21,33 Z" fill="#ffffff" />
        <g className="loader-flip">
          <circle cx="20" cy="16.5" r="8.3" fill="#ffffff" />
          <path
            d="M20,11.5 L21.411,14.558 L24.755,14.955 L22.283,17.242 L22.939,20.545 L20,18.9 L17.061,20.545 L17.717,17.242 L15.245,14.955 L18.589,14.558 Z"
            fill="url(#loader-bg)"
          />
        </g>

        <g clipPath="url(#loader-tile)">
          <rect className="loader-glint" x="-16" y="-10" width="12" height="60" fill="url(#loader-glint)" />
        </g>
        <rect x="0.7" y="0.7" width="38.6" height="38.6" rx="10.3" stroke="#ffffff" strokeOpacity="0.14" strokeWidth="1.2" />
      </svg>
      <span aria-hidden="true" className="loader-shadow h-1.5 w-12 rounded-full bg-primary/30 blur-[3px]" />
    </div>
  );
}
