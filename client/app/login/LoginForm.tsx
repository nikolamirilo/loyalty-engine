"use client";

import { useActionState } from "react";

import { idleState } from "@/lib/action-state";
import { login } from "@/lib/auth/actions";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Field, Input } from "@/components/ui/Field";
import { SubmitButton } from "@/components/ui/SubmitButton";

export function LoginForm() {
  const [state, formAction] = useActionState(login, idleState);

  return (
    <form action={formAction} className="space-y-4">
      <Field label="Username" htmlFor="username">
        <Input
          id="username"
          name="username"
          autoComplete="username"
          autoFocus
          required
        />
      </Field>
      <Field label="Password" htmlFor="password">
        <Input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </Field>
      {state.error && <ErrorBanner message={state.error} />}
      <SubmitButton className="w-full">Sign in</SubmitButton>
    </form>
  );
}
