"use client";

import { createContext, useContext } from "react";

/**
 * The logo of the program on screen, for components that render below a shell
 * but receive no props from it - chiefly the `loading.tsx` fallbacks, which
 * Next mounts inside the layout without letting it pass anything down.
 *
 * Null outside a shell, or when the program has no logo of its own.
 */
const ProgramLogoContext = createContext<string | null>(null);

export function ProgramLogoProvider({
  logoUrl,
  children,
}: {
  logoUrl: string | null | undefined;
  children: React.ReactNode;
}) {
  return (
    <ProgramLogoContext.Provider value={logoUrl || null}>{children}</ProgramLogoContext.Provider>
  );
}

export function useProgramLogo(): string | null {
  return useContext(ProgramLogoContext);
}
