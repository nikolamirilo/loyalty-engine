"use client";

import Link from "next/link";

import { createMember } from "@/lib/actions";
import { useMembersCount } from "@/lib/swr/hooks";
import { useRevalidate } from "@/lib/swr/revalidate";
import { Button, buttonClass } from "@/components/ui/Button";
import { FormDialog } from "@/components/ui/FormDialog";
import { PageHeader } from "@/components/ui/PageHeader";
import { MemberFields } from "@/components/members/MemberFields";
import { MembersView } from "@/components/members/MembersView";
import { PlusIcon, SlidersIcon } from "@/components/ui/icons";

function NewMemberButton() {
  const revalidate = useRevalidate();
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
      onSuccess={() => revalidate.members()}
    >
      <MemberFields />
    </FormDialog>
  );
}

export default function MembersPage() {
  // Total (unfiltered) count for the header; deduped with MembersView's own
  // count query when there's no active search.
  const { data: countData } = useMembersCount();
  const total = countData?.count;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Members"
        description={
          total != null
            ? `${total} member${total === 1 ? "" : "s"} in the program.`
            : "Loyalty program members."
        }
        actions={
          <>
            {/* A Link rather than a Button: a <button> nested in an <a> is
                invalid HTML, so this borrows the button styling instead. */}
            <Link
              href="/members/configure"
              className={buttonClass({ variant: "secondary" })}
            >
              <SlidersIcon /> Configure
            </Link>
            <NewMemberButton />
          </>
        }
      />
      <MembersView />
    </div>
  );
}
