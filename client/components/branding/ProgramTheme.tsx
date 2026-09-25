import { programThemeCss } from "@/lib/theme";
import type { Program } from "@/lib/types";

/**
 * Applies a program's brand colours to everything on the page, dialogs and
 * toasts included: it overrides the root colour tokens rather than wrapping a
 * subtree, since portals render outside any wrapper.
 *
 * Rendered by a layout, so it is only in the document while that layout is -
 * the console's theme never leaks into the member app or the other way round.
 * Renders nothing for a program on the stock theme.
 */
export function ProgramTheme({
  program,
}: {
  program: Pick<Program, "primaryColor" | "secondaryColor"> | null;
}) {
  const css = programThemeCss(program);
  if (!css) return null;
  // Safe to inject: programThemeCss only ever emits validated #rrggbb values.
  return <style dangerouslySetInnerHTML={{ __html: css }} />;
}
