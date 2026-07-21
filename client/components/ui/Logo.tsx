import type { SVGProps } from "react";

export function Logo(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
      {...props}
    >
      <defs>
        <linearGradient id="logo-bg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#3987e5" />
          <stop offset="1" stopColor="#1c5cab" />
        </linearGradient>
      </defs>

      <rect width="40" height="40" rx="10" fill="url(#logo-bg)" />

      <path
        d="M13.5 15.5C10.46 15.5 8 17.96 8 21s2.46 5.5 5.5 5.5c2.29 0 4.25-1.4 5.08-3.4.83 2 2.79 3.4 5.08 3.4 3.04 0 5.5-2.46 5.5-5.5s-2.46-5.5-5.5-5.5c-2.29 0-4.25 1.4-5.08 3.4-.83-2-2.79-3.4-5.08-3.4Z"
        stroke="#ffffff"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <path
        d="M20 8.5l1.15 2.9 2.9 1.15-2.9 1.15L20 16.6l-1.15-2.9-2.9-1.15 2.9-1.15L20 8.5Z"
        fill="#ffffff"
      />
    </svg>
  );
}
