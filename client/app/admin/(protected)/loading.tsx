import { LogoLoader } from "@/components/ui/LogoLoader";

/**
 * Navigation loader for the console. Because this lives inside the
 * admin/(protected) segment, Next wraps every protected page in a Suspense boundary *below* the
 * layout - so the AppShell sidebar stays on screen and only the content area
 * shows the loader while the page renders on the server and streams in.
 *
 * The height is the viewport less the chrome above and around the content
 * (mobile header + padding; just padding at `lg`, where the sidebar replaces
 * the header), so the loader sits on the content area's vertical center.
 */
export default function ProtectedLoading() {
  return (
    <div className="flex min-h-[calc(100dvh-6.5rem)] lg:min-h-[calc(100dvh-4rem)] items-center justify-center">
      <LogoLoader />
    </div>
  );
}
