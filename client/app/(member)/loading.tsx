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
 */
export default function MemberLoading() {
  return (
    <div className="flex min-h-[26rem] items-center justify-center">
      <LogoLoader />
    </div>
  );
}
