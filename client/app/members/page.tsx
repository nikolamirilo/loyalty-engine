import { createMember } from "@/lib/actions";
import { getMembers, getTiers } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { MemberFields } from "@/components/members/MemberFields";
import { MembersTable } from "@/components/members/MembersTable";
import { PlusIcon } from "@/components/ui/icons";

function NewMemberButton() {
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New member
        </Button>
      }
      title="New member"
      description="Add a member to the loyalty program."
      action={createMember}
      submitLabel="Create member"
    >
      <MemberFields />
    </FormDialog>
  );
}

export default async function MembersPage() {
  const [members, tiers] = await Promise.all([getMembers(), getTiers()]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Members"
        description={`${members.length} member${members.length === 1 ? "" : "s"} in the program.`}
        actions={<NewMemberButton />}
      />
      <Card className="overflow-hidden p-0">
        <MembersTable members={members} tiers={tiers} />
      </Card>
    </div>
  );
}
