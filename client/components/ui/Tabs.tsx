"use client";

import { useState } from "react";

import { cn } from "@/lib/format";

export interface TabItem {
  value: string;
  label: string;
  content: React.ReactNode;
}

/**
 * A minimal, controlled-internally tab switcher: a segmented control above
 * the active panel. Panels are plain `ReactNode`s (server-rendered JSX is
 * fine to pass in as a prop from a Server Component) - this component only
 * owns which one is visible, not how any of them are built.
 */
export function Tabs({
  tabs,
  defaultValue,
}: {
  tabs: TabItem[];
  /** Defaults to the first tab. */
  defaultValue?: string;
}) {
  const [active, setActive] = useState(defaultValue ?? tabs[0]?.value);
  const activeTab = tabs.find((t) => t.value === active) ?? tabs[0];

  return (
    <div>
      <div role="tablist" className="flex gap-1 rounded-lg bg-surface-2 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            type="button"
            role="tab"
            aria-selected={tab.value === activeTab?.value}
            onClick={() => setActive(tab.value)}
            className={cn(
              "flex-1 cursor-pointer rounded-md px-3 py-2 text-sm font-medium transition-colors",
              tab.value === activeTab?.value
                ? "bg-surface text-foreground shadow-sm"
                : "text-muted hover:text-foreground",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4">{activeTab?.content}</div>
    </div>
  );
}
