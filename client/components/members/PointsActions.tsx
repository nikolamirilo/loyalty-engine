import { adjustPoints, burnPoints, earnPoints } from "@/lib/actions";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button } from "@/components/ui/Button";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { ArrowDownIcon, ArrowUpIcon, SparklesIcon } from "@/components/ui/icons";

export function PointsActions({ memberId }: { memberId: string }) {
  const revalidate = useRevalidate();
  return (
    <div className="flex flex-wrap gap-2">
      <FormDialog
        trigger={
          <Button size="sm" variant="secondary">
            <ArrowUpIcon /> Earn
          </Button>
        }
        title="Earn points"
        description="Awards points; the member's tier multiplier is applied automatically."
        action={earnPoints}
        submitLabel="Add points"
        onSuccess={() => revalidate.members()}
      >
        <input type="hidden" name="member_id" value={memberId} />
        <Field label="Points" htmlFor="earn-points" hint="before multiplier">
          <Input
            id="earn-points"
            name="points"
            type="number"
            min={1}
            step={1}
            placeholder="100"
            required
            autoFocus
          />
        </Field>
        <Field label="Reason" htmlFor="earn-desc" hint="optional">
          <Input
            id="earn-desc"
            name="description"
            placeholder="e.g. Birthday bonus"
          />
        </Field>
      </FormDialog>

      <FormDialog
        trigger={
          <Button size="sm" variant="secondary">
            <ArrowDownIcon /> Burn
          </Button>
        }
        title="Burn points"
        description="Deducts points from the member's balance."
        action={burnPoints}
        submitLabel="Burn points"
        onSuccess={() => revalidate.members()}
      >
        <input type="hidden" name="member_id" value={memberId} />
        <Field label="Points" htmlFor="burn-points">
          <Input
            id="burn-points"
            name="points"
            type="number"
            min={1}
            step={1}
            placeholder="30"
            required
            autoFocus
          />
        </Field>
        <Field label="Reason" htmlFor="burn-desc" hint="optional">
          <Input
            id="burn-desc"
            name="description"
            placeholder="e.g. Redeemed via support"
          />
        </Field>
      </FormDialog>

      <FormDialog
        trigger={
          <Button size="sm" variant="secondary">
            <SparklesIcon /> Adjust
          </Button>
        }
        title="Adjust balance"
        description="Manual adjustment, positive or negative, with an optional note."
        action={adjustPoints}
        submitLabel="Apply adjustment"
        onSuccess={() => revalidate.members()}
      >
        <input type="hidden" name="member_id" value={memberId} />
        <Field label="Amount" htmlFor="adjust-points" help="Use a negative value to subtract">
          <Input
            id="adjust-points"
            name="points"
            type="number"
            step={1}
            placeholder="e.g. -50"
            required
            autoFocus
          />
        </Field>
        <Field label="Reason" htmlFor="adjust-desc" hint="optional">
          <Input
            id="adjust-desc"
            name="description"
            placeholder="e.g. Goodwill credit"
          />
        </Field>
      </FormDialog>
    </div>
  );
}
