import { toDatetimeLocalValue } from "@/lib/format";
import type { Challenge, Reward } from "@/lib/types";
import { Checkbox, Field, Input, Select, Textarea } from "@/components/ui/Field";

/** Shared form fields for creating and editing a challenge. */
export function ChallengeFields({
  challenge,
  rewards,
}: {
  challenge?: Challenge;
  rewards: Reward[];
}) {
  return (
    <>
      <Field label="Name" htmlFor="challenge-name">
        <Input
          id="challenge-name"
          name="name"
          placeholder="e.g. Refer 3 friends"
          defaultValue={challenge?.name}
          required
        />
      </Field>
      <Field label="Description" htmlFor="challenge-desc">
        <Textarea
          id="challenge-desc"
          name="description"
          placeholder="Optional details"
          defaultValue={challenge?.description ?? ""}
        />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field
          label="Target"
          htmlFor="challenge-target"
          help="Progress needed to complete"
        >
          <Input
            id="challenge-target"
            name="target_value"
            type="number"
            min={1}
            step={1}
            defaultValue={challenge?.target_value ?? 1}
            required
          />
        </Field>
        <Field
          label="Reward points"
          htmlFor="challenge-points"
          help="Granted on completion"
        >
          <Input
            id="challenge-points"
            name="reward_points"
            type="number"
            min={0}
            step={1}
            defaultValue={challenge?.reward_points ?? 0}
          />
        </Field>
      </div>
      <Field label="Prize reward" htmlFor="challenge-reward" help="Optional - assigned on completion">
        <Select
          id="challenge-reward"
          name="reward_id"
          defaultValue={challenge?.reward_id ?? ""}
        >
          <option value="">No prize</option>
          {rewards.map((reward) => (
            <option key={reward.id} value={reward.id}>
              {reward.name}
            </option>
          ))}
        </Select>
      </Field>
      <Field label="Expires at" htmlFor="challenge-expires" help="Optional deadline">
        <Input
          id="challenge-expires"
          name="expires_at"
          type="datetime-local"
          defaultValue={toDatetimeLocalValue(challenge?.expires_at)}
        />
      </Field>
      <Checkbox
        name="is_active"
        label="Active (can be assigned)"
        defaultChecked={challenge ? challenge.is_active : true}
      />
    </>
  );
}
