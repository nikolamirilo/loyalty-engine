import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";

/**
 * Navigation skeleton for the console. Because this lives inside the (protected)
 * segment, Next wraps every protected page in a Suspense boundary *below* the
 * layout — so the AppShell sidebar stays on screen and only the content area
 * shows this skeleton while the page renders on the server and streams in.
 *
 * The shape (header + stat tiles + a list) mirrors the busiest pages; it is
 * shown only for the brief moment before real content replaces it.
 */
export default function ProtectedLoading() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Loading">
      {/* Page header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2.5">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-9 w-32 rounded-lg" />
      </div>

      {/* Stat tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-3">
                <Skeleton className="h-3.5 w-20" />
                <Skeleton className="h-8 w-16" />
              </div>
              <Skeleton className="h-10 w-10 rounded-lg" />
            </div>
          </Card>
        ))}
      </div>

      {/* Main content block (table / cards) */}
      <Card className="overflow-hidden">
        <div className="border-b border-line px-5 py-4">
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="divide-y divide-line">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-4">
              <Skeleton className="h-9 w-9 rounded-full" />
              <div className="min-w-0 flex-1 space-y-2">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-3 w-56" />
              </div>
              <Skeleton className="h-6 w-16 rounded-full" />
              <Skeleton className="h-4 w-12" />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
