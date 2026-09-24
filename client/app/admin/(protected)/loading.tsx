import { LogoLoader } from "@/components/ui/LogoLoader";

/**
 * Navigation loader for the console. Because this lives inside the
 * admin/(protected) segment, Next wraps every protected page in a Suspense boundary *below* the
 * layout - so the AppShell sidebar stays on screen and only the content area
 * shows the loader while the page renders on the server and streams in.
 */
export default function ProtectedLoading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <LogoLoader />
    </div>
  );
}
