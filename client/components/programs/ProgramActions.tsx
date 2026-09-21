"use client";

import { createProgram, removeProgram, updateProgram } from "@/lib/programs/actions";
import type { Program } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { Field, Input } from "@/components/ui/Field";
import { FormDialog } from "@/components/ui/FormDialog";
import { useToast } from "@/components/ui/Toast";
import { CopyIcon, PencilIcon, PlusIcon, TrashIcon } from "@/components/ui/icons";

/** Shared between the create and edit dialogs. */
function ProgramFields({ program }: { program?: Program }) {
  return (
    <>
      <Field label="Name" htmlFor="program-name">
        <Input
          id="program-name"
          name="name"
          placeholder="e.g. Retail Demo"
          defaultValue={program?.name}
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
          defaultValue={program?.slug}
          required
        />
      </Field>
      <Field label="Description" htmlFor="program-description">
        <Input
          id="program-description"
          name="description"
          placeholder="What this demo is for"
          defaultValue={program?.description ?? ""}
        />
      </Field>
    </>
  );
}

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
      <ProgramFields />
    </FormDialog>
  );
}

/** The program id is what API calls address a program by, so it is worth one
 * click to get hold of. Icon-only like the edit and delete buttons it sits
 * beside - the id itself stays off screen, the slug next to the name is the
 * readable handle. */
export function CopyProgramIdButton({ program }: { program: Program }) {
  const toast = useToast();

  const copyId = async () => {
    try {
      await navigator.clipboard.writeText(program.id);
      toast.success("Program ID copied.");
    } catch {
      toast.error("Couldn't copy program ID.");
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={copyId}
      aria-label={`Copy ID for ${program.name}`}
      title="Copy program ID"
    >
      <CopyIcon />
    </Button>
  );
}

export function EditProgramButton({ program }: { program: Program }) {
  return (
    <FormDialog
      trigger={
        <Button variant="ghost" size="icon" aria-label={`Edit ${program.name}`}>
          <PencilIcon />
        </Button>
      }
      title={`Edit ${program.name}`}
      action={updateProgram}
      submitLabel="Save changes"
    >
      <input type="hidden" name="id" value={program.id} />
      <ProgramFields program={program} />
      {/* Already the default: unchecking it here would leave no program for a
          request without a header to land on, so promote another instead. The
          box is disabled to say so - and a disabled input is not submitted, so
          this carries the value that saving must not silently drop. */}
      {program.isDefault && <input type="hidden" name="isDefault" value="on" />}
      <label className="flex items-center gap-2 text-sm text-foreground">
        <input
          type="checkbox"
          name="isDefault"
          defaultChecked={program.isDefault}
          disabled={program.isDefault}
          className="h-4 w-4 cursor-pointer rounded border-line"
        />
        Use as the default program
      </label>
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
