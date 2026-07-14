import type { Reward } from "@/lib/types";
import { Checkbox, Field, Input, Textarea } from "@/components/ui/Field";

/** Shared form fields for creating and editing a reward. */
export function RewardFields({ reward }: { reward?: Reward }) {
  return (
    <>
      <Field label="Name" htmlFor="reward-name">
        <Input
          id="reward-name"
          name="name"
          placeholder="e.g. $10 gift card"
          defaultValue={reward?.name}
          required
        />
      </Field>
      <Field label="Description" htmlFor="reward-desc">
        <Textarea
          id="reward-desc"
          name="description"
          placeholder="Optional details shown to members"
          defaultValue={reward?.description ?? ""}
        />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Points cost" htmlFor="reward-cost" hint="> 0">
          <Input
            id="reward-cost"
            name="points_cost"
            type="number"
            min={1}
            step={1}
            defaultValue={reward?.points_cost}
            required
          />
        </Field>
        <Field label="Stock" htmlFor="reward-stock" help="Leave blank for unlimited">
          <Input
            id="reward-stock"
            name="stock"
            type="number"
            min={0}
            step={1}
            defaultValue={reward?.stock ?? ""}
          />
        </Field>
      </div>
      <Checkbox
        name="is_active"
        label="Active (available to redeem)"
        defaultChecked={reward ? reward.is_active : true}
      />
    </>
  );
}
