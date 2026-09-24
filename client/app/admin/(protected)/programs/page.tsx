import { getPrograms } from "@/lib/api";
import { activeProgramId } from "@/lib/server/program";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { switchProgram } from "@/lib/programs/actions";
import { Button } from "@/components/ui/Button";
import {
  CopyProgramIdButton,
  DeleteProgramButton,
  EditProgramButton,
  NewProgramButton,
} from "@/components/programs/ProgramActions";

/**
 * Programs are the isolation boundary: each one is a self-contained loyalty
 * program with its own rewards, products, challenges, tiers, segments and
 * member balances. Nothing inside one program is visible from another.
 */
export default async function ProgramsPage() {
  const [programs, selected] = await Promise.all([
    getPrograms(),
    activeProgramId(),
  ]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Programs"
        description="Each program has its own rewards, products, challenges, tiers and member points. Switching programs in the sidebar changes everything the console shows."
        actions={<NewProgramButton />}
      />

      {programs.length === 0 ? (
        <Card className="p-8 text-center text-sm text-muted">
          No programs yet. Create one to start adding rewards, challenges and tiers.
        </Card>
      ) : (
        <ul className="space-y-3">
          {programs.map((program) => {
            const active =
              program.slug === selected || program.id === selected;
            return (
              <li key={program.id}>
                <Card className="flex items-center justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-foreground">
                        {program.name}
                      </span>
                      <code className="rounded bg-surface-2 px-1.5 py-0.5 text-xs text-muted">
                        {program.slug}
                      </code>
                      {program.isDefault && (
                        <span className="rounded-full bg-primary-subtle px-2 py-0.5 text-xs font-medium text-primary-subtle-fg">
                          Default
                        </span>
                      )}
                      {active && (
                        <span className="text-xs font-medium text-muted">
                          Currently viewing
                        </span>
                      )}
                    </div>
                    {program.description && (
                      <p className="mt-1 truncate text-sm text-muted">
                        {program.description}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    {!active && (
                      <form action={switchProgram}>
                        <input type="hidden" name="slug" value={program.slug} />
                        <Button type="submit" variant="secondary" size="sm">
                          Switch to
                        </Button>
                      </form>
                    )}
                    <CopyProgramIdButton program={program} />
                    <EditProgramButton program={program} />
                    {/* The default program is what a request with no program
                        header falls back to, so the API refuses to delete it. */}
                    {!program.isDefault && (
                      <DeleteProgramButton program={program} />
                    )}
                  </div>
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
