"use client";

import { useFormStatus } from "react-dom";

import { Button, type ButtonProps } from "./Button";

/** A submit button that reflects the enclosing form's pending state. */
export function SubmitButton({ children, ...props }: ButtonProps) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" loading={pending} {...props}>
      {children}
    </Button>
  );
}
