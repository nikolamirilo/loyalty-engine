import { LogoLoader } from "@/components/ui/LogoLoader";

/**
 * Navigation loader for the member tab shell, mirroring the admin console's
 * loading.tsx. It sits inside the `(member)` segment, so Next wraps each tab's
 * page in a Suspense boundary *below* MemberShell - the header and tab bar stay
 * put and only the content area swaps while the page streams in.
 *
 * This file is also what makes the tabs prefetchable. Per Next's prefetching
 * rules, a dynamic route (all these tabs read the member session cookie) is
 * only prefetched down to its nearest loading boundary; without one, there is
 * nothing to prefetch and every tab switch waits on a full server round-trip.
 *
 * `absolute inset-0` fills the content region between the header and the tab
 * bar (MemberShell's `<main>` is `relative` for exactly this), so the loader
 * sits on its true center whatever the screen height.
 */
export default function MemberLoading() {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <LogoLoader />
    </div>
  );
}
