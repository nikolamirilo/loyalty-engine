import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // Keep recently-visited pages in the client-side Router Cache so navigating
    // back to a page you were just on is instant, with no server round-trip.
    // Dynamic pages default to 0 (no client cache), which is why every
    // navigation re-fetched from the API. Mutations call revalidatePath (see
    // lib/actions.ts), which busts these caches, so edits never show stale data.
    staleTimes: {
      dynamic: 30,
      static: 180,
    },
  },
};

export default nextConfig;
