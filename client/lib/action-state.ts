// Shared result type for Server Actions. Kept in a plain module because a
// "use server" file may only export async functions.

export type ActionState = { ok: boolean; error?: string; message?: string };

/** Initial state for `useActionState` - neither success nor error yet. */
export const idleState: ActionState = { ok: false };
