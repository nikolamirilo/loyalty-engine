"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { TargetIcon } from "@/components/ui/icons";

/** Appends the signed-in member's id as `userId` on the campaign URL, adding
 * to any query string it already has. */
function withMemberId(rawUrl: string, memberId: string): string {
  const url = new URL(rawUrl);
  url.searchParams.set("userId", memberId);
  return url.toString();
}

export function CampaignLauncher({ memberId }: { memberId: string }) {
  const [campaignUrl, setCampaignUrl] = useState("");
  const toast = useToast();

  const openCampaign = () => {
    const trimmed = campaignUrl.trim();
    if (!trimmed) {
      toast.error("Enter a campaign URL.");
      return;
    }

    let finalUrl: string;
    try {
      finalUrl = withMemberId(trimmed, memberId);
    } catch {
      toast.error("Enter a valid campaign URL.");
      return;
    }

    window.open(finalUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <Card>
      <CardHeader
        title="Campaigns"
        description="Open a campaign link with your user ID attached."
      />
      <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-end">
        <Field label="Campaign URL" className="flex-1">
          <Input
            type="url"
            placeholder="https://example.com/campaign"
            value={campaignUrl}
            onChange={(e) => setCampaignUrl(e.target.value)}
          />
        </Field>
        <Button onClick={openCampaign}>
          <TargetIcon /> Open campaign
        </Button>
      </div>
    </Card>
  );
}
