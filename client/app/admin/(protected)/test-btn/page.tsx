import { getMembers, getTiers } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { FormDialog } from "@/components/ui/FormDialog";
import { idleState, type ActionState } from "@/lib/action-state";

async function noop(prev: ActionState, fd: FormData): Promise<ActionState> {
  "use server";
  return idleState;
}

export default async function TestBtn() {
  const [members, tiers] = await Promise.all([getMembers(), getTiers()]);
  return (
    <div>
      <p>{members.length} / {tiers.length}</p>
      <FormDialog trigger={<Button>Open</Button>} title="Test" action={noop}>
        <div>hi</div>
      </FormDialog>
    </div>
  );
}
