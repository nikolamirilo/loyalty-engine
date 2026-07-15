/** Client-safe API error (mirrors lib/api.ts's ApiError without the server-only
 * token dependency, so it can be imported into Client Components). */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}
