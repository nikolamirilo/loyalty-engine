import path from "node:path";

import type { NextConfig } from "next";

// This app is its own project root. The repo root holds a second
// package-lock.json (husky only, see ../package.json), which Next would
// otherwise pick as the root - warning about "additional lockfiles" and
// widening file watching and output tracing to the whole repo.
const projectRoot = path.resolve(__dirname);

const nextConfig: NextConfig = {
  turbopack: { root: projectRoot },
  outputFileTracingRoot: projectRoot,
  experimental: {
    // Program logos are uploaded through a Server Action (lib/programs/actions.ts)
    // and may be up to 2 MB - the API's own limit - which the 1 MB default
    // would refuse before the action ran. The extra room covers the multipart
    // framing and the rest of the form.
    serverActions: {
      bodySizeLimit: "3mb",
    },
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
