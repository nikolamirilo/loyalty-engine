import { AlertTriangleIcon } from "./icons";

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-danger/30 bg-danger-subtle px-3 py-2 text-[13px] text-danger-fg">
      <AlertTriangleIcon className="mt-0.5 shrink-0 text-sm" />
      <span>{message}</span>
    </div>
  );
}
