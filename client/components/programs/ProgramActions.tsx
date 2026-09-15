"use client";

import { createProgram, removeProgram } from "@/lib/programs/actions";
import type { Program } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { PlusIcon, TrashIcon } from "@/components/ui/icons";

export function NewProgramButton() {
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New program
        </Button>
      }
      title="New program"
      description="A program starts empty: its own rewards, products, challenges, tiers, segments and members."
      action={createProgram}
      submitLabel="Create program"
    >
      <Field label="Name" htmlFor="program-name">
        <Input
          id="program-name"
          name="name"
          placeholder="e.g. Retail Demo"
          required
        />
      </Field>
      <Field
        label="Slug"
        htmlFor="program-slug"
        hint="Lowercase letters, numbers and hyphens. Used to address the program in API calls."
      >
        <Input
          id="program-slug"
          name="slug"
          placeholder="e.g. retail-demo"
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          required
        />
      </Field>
      <Field label="Description" htmlFor="program-description">
        <Input
          id="program-description"
          name="description"
          placeholder="What this demo is for"
        />
      </Field>
    </FormDialog>
  );
}

export function DeleteProgramButton({ program }: { program: Program }) {
  return (
    <ConfirmButton
      trigger={
        <Button variant="ghost" size="icon" aria-label={`Delete ${program.name}`}>
          <TrashIcon />
        </Button>
      }
      title={`Delete ${program.name}?`}
      description="Everything inside it goes too: members, points, rewards, products, challenges, tiers and segments. People keep their accounts and any memberships in other programs."
      confirmLabel="Delete program"
      action={() => removeProgram(program.id)}
    />
  );
}
