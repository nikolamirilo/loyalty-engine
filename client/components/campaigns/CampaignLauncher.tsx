"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { Field, Input } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { TargetIcon, XIcon } from "@/components/ui/icons";

/** Appends the signed-in member's id as `userId` on the campaign URL, adding
 * to any query string it already has. */
function withMemberId(rawUrl: string, memberId: string): string {
  const url = new URL(rawUrl);
  url.searchParams.set("userId", memberId);
  return url.toString();
}

export function CampaignLauncher({ memberId }: { memberId: string }) {
  const [campaignUrl, setCampaignUrl] = useState("");
  const [loadedUrl, setLoadedUrl] = useState<string | null>(null);
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

    setLoadedUrl(finalUrl);
  };

  return (
    <Card>
      <CardHeader
        title="Campaigns"
        description="Load a campaign link with your user ID attached."
        action={
          loadedUrl && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setLoadedUrl(null)}
            >
              <XIcon /> Close
            </Button>
          )
        }
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
      {loadedUrl && (
        <iframe
          key={loadedUrl}
          src={loadedUrl}
          title="Campaign"
          className="h-[70vh] w-full border-t border-line"
        />
      )}
    </Card>
  );
}
