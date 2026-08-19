"use client";

import Link from "next/link";

import {
  createMemberAttribute,
  deleteMemberAttribute,
  updateMemberAttribute,
} from "@/lib/actions";
import {
  ATTRIBUTE_TYPE_LABELS,
  formatCustomValue,
} from "@/lib/custom-attributes";
import { useMemberAttributes } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import type { MemberAttribute } from "@/lib/types";
import { AttributeFields } from "@/components/members/attributes/AttributeFields";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { ConfirmButton } from "@/components/ui/ConfirmButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/Table";
import {
  ChevronRightIcon,
  PencilIcon,
  PlusIcon,
  SlidersIcon,
  TrashIcon,
} from "@/components/ui/icons";

/** The fields every member has. Not stored in `member_attributes` - the app
 *  knows them at build time, and they're listed here so the Configure page shows
 *  the complete member shape rather than only the custom part. */
const BUILT_IN = [
  { label: "Name", type: "Text", note: "Required" },
  { label: "Email", type: "Text", note: "Required, unique" },
  { label: "Phone", type: "Text" },
  { label: "Tier", type: "Reference", note: "Derived from points balance" },
  { label: "Points balance", type: "Number", note: "Managed by points actions" },
  { label: "Segments", type: "Multi-reference", note: "Managed on the Segments page" },
];

function useAttributesMutated() {
  const revalidate = useRevalidate();
  // Creating an attribute with a default backfills every member, and deleting one
  // strips the key - so member caches are stale too, not just the definitions.
  return () => {
    revalidate.memberAttributes();
    revalidate.members();
  };
}

function NewAttributeButton() {
  const onMutated = useAttributesMutated();
  return (
    <FormDialog
      trigger={
        <Button>
          <PlusIcon /> New custom attribute
        </Button>
      }
      title="New custom attribute"
      description="Adds a field to every member. Custom attributes are always optional."
      action={createMemberAttribute}
      submitLabel="Create attribute"
      onSuccess={onMutated}
    >
      <AttributeFields />
    </FormDialog>
  );
}

function AttributeRowActions({ attribute }: { attribute: MemberAttribute }) {
  const onMutated = useAttributesMutated();
  return (
    <div className="flex justify-end gap-2">
      <FormDialog
        trigger={
          <Button variant="secondary" size="sm">
            <PencilIcon /> Edit
          </Button>
        }
        title={`Edit ${attribute.label}`}
        description="The name and default value can change; the type and internal key can't."
        action={updateMemberAttribute}
        submitLabel="Save changes"
        onSuccess={onMutated}
      >
        <input type="hidden" name="id" value={attribute.id} />
        <AttributeFields attribute={attribute} />
      </FormDialog>
      <ConfirmButton
        trigger={
          <Button variant="secondary" size="sm" className="text-danger">
            <TrashIcon /> Delete
          </Button>
        }
        title={`Delete ${attribute.label}?`}
        description="This removes the field and its stored value from every member. It can't be undone."
        confirmLabel="Delete attribute"
        action={deleteMemberAttribute.bind(null, attribute.id)}
        successMessage="Custom attribute deleted."
        onSuccess={onMutated}
      />
    </div>
  );
}

export default function ConfigureMembersPage() {
  const { data: attributes } = useMemberAttributes();

  return (
    <div className="space-y-6">
      <Link
        href="/members"
        className="inline-flex items-center gap-1 text-sm text-muted transition-colors hover:text-foreground"
      >
        <ChevronRightIcon className="rotate-180 text-base" />
        All members
      </Link>

      <PageHeader
        title="Member fields"
        description="Every field on a member. Built-in fields are fixed; custom attributes are yours to add, rename, and remove."
      />

      <Card>
        <CardHeader
          title="Built-in fields"
          description="Part of the loyalty engine itself - these can't be changed or removed."
        />
        <Table>
          <THead>
            <TR>
              <TH>Field</TH>
              <TH>Type</TH>
              <TH>Notes</TH>
            </TR>
          </THead>
          <TBody>
            {BUILT_IN.map((field) => (
              <TR key={field.label}>
                <TD>
                  <span className="flex items-center gap-2">
                    <span className="font-medium">{field.label}</span>
                    <Badge tone="neutral">Built-in</Badge>
                  </span>
                </TD>
                <TD className="text-muted">{field.type}</TD>
                <TD className="text-muted">{field.note ?? "-"}</TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </Card>

      <Card>
        <CardHeader
          title="Custom attributes"
          description="Applied to every member. Always optional - a member can leave any of them empty."
          action={attributes && attributes.length > 0 ? <NewAttributeButton /> : undefined}
        />
        {attributes === undefined ? (
          <div className="space-y-3 p-5">
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-2/3" />
          </div>
        ) : attributes.length === 0 ? (
          <EmptyState
            icon={<SlidersIcon />}
            title="No custom attributes yet"
            description="Add a field like Birthday or Favourite store to track it on every member."
            action={<NewAttributeButton />}
          />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Field</TH>
                <TH>Type</TH>
                <TH>Default</TH>
                <TH className="text-right">Actions</TH>
              </TR>
            </THead>
            <TBody>
              {attributes.map((attribute) => (
                <TR key={attribute.id} className="hover:bg-surface-2/60">
                  <TD>
                    <span className="block font-medium">{attribute.label}</span>
                    <code className="block text-xs text-faint">{attribute.key}</code>
                  </TD>
                  <TD className="text-muted">
                    {ATTRIBUTE_TYPE_LABELS[attribute.type]}
                    {attribute.type === "select" && attribute.options?.length ? (
                      <span className="block text-xs text-faint">
                        {attribute.options.join(", ")}
                      </span>
                    ) : null}
                  </TD>
                  <TD className="text-muted">
                    {formatCustomValue(attribute, attribute.default_value) ?? (
                      <span className="text-faint">-</span>
                    )}
                  </TD>
                  <TD>
                    <AttributeRowActions attribute={attribute} />
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
