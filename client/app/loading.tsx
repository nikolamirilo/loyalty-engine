import { Spinner } from "@/components/ui/Spinner";

export default function Loading() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-primary">
      <Spinner className="text-6xl" />
    </div>
  );
}
