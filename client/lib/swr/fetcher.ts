import { ApiError } from "./error";

/**
 * Browser data fetcher for SWR. Every read goes through the same-origin proxy
 * (`/api/le/*`), which attaches the server-only API token. The SWR key is the
 * upstream path + query (e.g. "/members?limit=10"), so it doubles as a stable,
 * human-readable cache key.
 */
export async function fetcher<T>(key: string): Promise<T> {
  const res = await fetch(`/api/le${key}`, {
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    throw new ApiError(res.status, await errorMessage(res));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Pull a human message out of a FastAPI error body ({ detail } shapes). */
async function errorMessage(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json();
    if (data && typeof data === "object" && "detail" in data) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail)) {
        const msgs = detail
          .map((d) =>
            d && typeof d === "object" && "msg" in d
              ? String((d as { msg: unknown }).msg)
              : null,
          )
          .filter(Boolean);
        if (msgs.length) return msgs.join(", ");
      }
    }
  } catch {
    /* non-JSON error body — fall through to the generic message */
  }
  return `Request failed (${res.status}).`;
}
