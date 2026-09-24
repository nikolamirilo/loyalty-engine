import { EventDetail } from "@/components/events/EventDetail";

export default async function EventPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EventDetail id={id} />;
}
