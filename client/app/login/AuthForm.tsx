"use client";

import { useActionState, useEffect, useState } from "react";

import { idleState } from "@/lib/action-state";
import {
  requestLoginCode,
  requestSignupCode,
  verifyLoginCode,
} from "@/lib/memberAuth/actions";
import { cn } from "@/lib/format";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Field, Input } from "@/components/ui/Field";
import { SubmitButton } from "@/components/ui/SubmitButton";

type Mode = "login" | "signup";

/** Step 1 of the flow: collect email (+ name/phone for signup) and send the code. */
function RequestForm({
  mode,
  onSent,
}: {
  mode: Mode;
  onSent: (email: string) => void;
}) {
  const action = mode === "login" ? requestLoginCode : requestSignupCode;
  const [state, formAction] = useActionState(action, idleState);
  const [pendingEmail, setPendingEmail] = useState("");

  // Transition to the code step once the code has actually been sent.
  useEffect(() => {
    if (state.ok) onSent(pendingEmail);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state]);

  return (
    <form
      action={formAction}
      onSubmit={(e) =>
        setPendingEmail(String(new FormData(e.currentTarget).get("email") ?? "").trim())
      }
      className="space-y-4"
    >
      {mode === "signup" && (
        <Field label="Name" htmlFor="name">
          <Input id="name" name="name" autoComplete="name" required />
        </Field>
      )}
      <Field label="Email" htmlFor="email">
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          autoFocus
          required
        />
      </Field>
      {mode === "signup" && (
        <Field label="Phone" htmlFor="phone" hint="Optional">
          <Input id="phone" name="phone" type="tel" autoComplete="tel" />
        </Field>
      )}
      {state.error && <ErrorBanner message={state.error} />}
      <SubmitButton className="w-full">
        {mode === "login" ? "Send login code" : "Create account"}
      </SubmitButton>
    </form>
  );
}

/**
 * Two-step member entry: request a login code (email only, or email + name +
 * optional phone for signup), then enter the 6-digit code that was emailed.
 *
 * `resetKey` remounts `RequestForm` (and so its `useActionState`) whenever
 * the member switches mode or backs out of the code step - without it, a
 * stale `state.ok === true` from the previous successful send would bounce
 * the member straight back to the code step.
 */
export function AuthForm() {
  const [mode, setMode] = useState<Mode>("login");
  const [step, setStep] = useState<"request" | "code">("request");
  const [email, setEmail] = useState("");
  const [resetKey, setResetKey] = useState(0);
  const [verifyState, verifyAction] = useActionState(verifyLoginCode, idleState);

  if (step === "code") {
    return (
      <form action={verifyAction} className="space-y-4">
        <input type="hidden" name="email" value={email} />
        <p className="text-center text-sm text-muted">
          We sent a 6-digit code to{" "}
          <span className="font-medium text-foreground">{email}</span>.
        </p>
        <Field label="Code" htmlFor="code">
          <Input
            id="code"
            name="code"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            autoFocus
            required
          />
        </Field>
        {verifyState.error && <ErrorBanner message={verifyState.error} />}
        <SubmitButton className="w-full">Continue</SubmitButton>
        <button
          type="button"
          onClick={() => {
            setStep("request");
            setResetKey((k) => k + 1);
          }}
          className="w-full cursor-pointer text-center text-[0.8125rem] text-muted hover:text-foreground"
        >
          Use a different email
        </button>
      </form>
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-1 rounded-lg bg-surface-2 p-1">
        {(["login", "signup"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => {
              setMode(m);
              setResetKey((k) => k + 1);
            }}
            className={cn(
              "cursor-pointer rounded-md py-1.5 text-sm font-medium transition-colors",
              mode === m
                ? "bg-surface text-foreground shadow-sm"
                : "text-muted hover:text-foreground",
            )}
          >
            {m === "login" ? "Log in" : "Sign up"}
          </button>
        ))}
      </div>

      <RequestForm
        key={`${mode}-${resetKey}`}
        mode={mode}
        onSent={(sentEmail) => {
          setEmail(sentEmail);
          setStep("code");
        }}
      />
    </div>
  );
}
