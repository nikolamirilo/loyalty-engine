import { Spinner } from "@/components/ui/Spinner";

export default function Loading() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 text-primary">
      <Spinner className="text-6xl" />
    </div>
  );
}
