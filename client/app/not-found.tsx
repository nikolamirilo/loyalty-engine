import Link from "next/link";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Card className="max-w-md p-8 text-center">
        <p className="text-5xl font-semibold tracking-tight text-foreground">
          404
        </p>
        <p className="mt-2 text-sm text-muted">
          We couldn&apos;t find the page you&apos;re looking for.
        </p>
        <div className="mt-6 flex justify-center">
          <Link href="/">
            <Button>Back to dashboard</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
