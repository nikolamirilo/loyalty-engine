"use client";

import { useCampaign } from "./CampaignContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";
import { TargetIcon } from "@/components/ui/icons";

/**
 * Home's content: the URL box that starts a campaign.
 *
 * The campaign itself is rendered by CampaignFrame up in MemberShell so it can
 * outlive navigation, which is why this component is only the form - once a
 * campaign is open there is nothing here to show, and the frame covers this
 * area anyway.
 */
export function CampaignLauncher() {
  const { draftUrl, setDraftUrl, loadedUrl, open, restored } = useCampaign();

  // Nothing to show until we know whether a campaign was left open, and
  // nothing to show while one is open.
  if (!restored || loadedUrl) return null;

  return (
    <Card className="p-5">
      <div className="flex flex-col gap-3">
        <Field label="Campaign URL">
          <Input
            type="url"
            placeholder="https://example.com/campaign"
            value={draftUrl}
            onChange={(e) => setDraftUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") open();
            }}
          />
        </Field>
        <Button onClick={open}>
          <TargetIcon /> Open campaign
        </Button>
      </div>
    </Card>
  );
}
