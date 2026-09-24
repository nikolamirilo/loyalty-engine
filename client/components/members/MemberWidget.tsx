import { Card, CardHeader } from "@/components/ui/Card";

/**
 * A member-detail widget. From laptop up every widget has the same fixed
 * height and its body scrolls, so a long list never stretches the widget
 * beside it or pushes the rest of the page down.
 */
export function MemberWidget({
  title,
  description,
  action,
  children,
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card className="flex flex-col overflow-hidden lg:h-[26rem]">
      <CardHeader title={title} description={description} action={action} />
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </Card>
  );
}
