"use client";

import { useState } from "react";
import type { KeyboardEvent } from "react";

import { cn } from "@/lib/format";
import { XIcon } from "@/components/ui/icons";

const CONTROL =
  "flex w-full flex-wrap items-center gap-1.5 rounded-lg border border-line bg-surface px-2 py-1.5 " +
  "text-sm text-foreground transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/25";

/** Labels-style input: type a value and press Enter or "," to add it as a tag. */
export function TagsInput({
  id,
  name,
  defaultValue = [],
  placeholder,
  className,
}: {
  id?: string;
  name: string;
  defaultValue?: string[];
  placeholder?: string;
  className?: string;
}) {
  const [tags, setTags] = useState<string[]>(defaultValue);
  const [draft, setDraft] = useState("");

  function addTag(raw: string) {
    const value = raw.trim();
    if (!value || tags.includes(value)) return;
    setTags((prev) => [...prev, value]);
    setDraft("");
  }

  function removeTag(value: string) {
    setTags((prev) => prev.filter((tag) => tag !== value));
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(draft);
    } else if (e.key === "Backspace" && draft === "" && tags.length > 0) {
      removeTag(tags[tags.length - 1]);
    }
  }

  return (
    <div className={cn(CONTROL, className)}>
      {tags.map((tag) => (
        <span
          key={tag}
          className="flex items-center gap-1 rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
        >
          {tag}
          <input type="hidden" name={name} value={tag} />
          <button
            type="button"
            onClick={() => removeTag(tag)}
            className="rounded-full text-primary/70 hover:text-primary"
            aria-label={`Remove ${tag}`}
          >
            <XIcon className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        id={id}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => addTag(draft)}
        placeholder={tags.length === 0 ? placeholder : undefined}
        className="min-w-[8ch] flex-1 bg-transparent py-0.5 text-sm text-foreground placeholder:text-faint focus-visible:outline-none"
      />
    </div>
  );
}
