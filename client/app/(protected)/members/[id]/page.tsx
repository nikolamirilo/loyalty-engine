import { MemberDetail } from "@/components/members/MemberDetail";

/**
 * Thin server wrapper: it only resolves the route param and renders the client
 * detail view. Because it awaits nothing else, navigation is instant — the
 * client component mounts immediately and streams each section in with its own
 * skeleton instead of blocking the click on the slowest API call.
 */
export default async function MemberPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <MemberDetail id={id} />;
}
