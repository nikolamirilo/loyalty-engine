import type { ChallengeStatus, TransactionType } from "@/lib/types";
import { Badge } from "./Badge";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  BanIcon,
  BoltIcon,
  CheckCircleIcon,
  ClockIcon,
  SparklesIcon,
} from "./icons";

type Tone = "neutral" | "primary" | "success" | "warning" | "danger";

// Status colors always ship with an icon + label — never color alone.
const CHALLENGE: Record<
  ChallengeStatus,
  { tone: Tone; label: string; Icon: (p: { className?: string }) => React.ReactElement }
> = {
  assigned: { tone: "neutral", label: "Assigned", Icon: ClockIcon },
  in_progress: { tone: "primary", label: "In progress", Icon: BoltIcon },
  completed: { tone: "success", label: "Completed", Icon: CheckCircleIcon },
  expired: { tone: "warning", label: "Expired", Icon: ClockIcon },
  cancelled: { tone: "danger", label: "Cancelled", Icon: BanIcon },
};

export function ChallengeStatusBadge({ status }: { status: ChallengeStatus }) {
  const { tone, label, Icon } = CHALLENGE[status];
  return (
    <Badge tone={tone}>
      <Icon className="text-[13px]" />
      {label}
    </Badge>
  );
}

const TRANSACTION: Record<
  TransactionType,
  { tone: Tone; label: string; Icon: (p: { className?: string }) => React.ReactElement }
> = {
  earn: { tone: "success", label: "Earn", Icon: ArrowUpIcon },
  spend: { tone: "danger", label: "Spend", Icon: ArrowDownIcon },
  adjust: { tone: "primary", label: "Adjust", Icon: SparklesIcon },
};

export function TransactionBadge({ type }: { type: TransactionType }) {
  const { tone, label, Icon } = TRANSACTION[type];
  return (
    <Badge tone={tone}>
      <Icon className="text-[13px]" />
      {label}
    </Badge>
  );
}

export function ActiveBadge({ active }: { active: boolean }) {
  return active ? (
    <Badge tone="success">
      <CheckCircleIcon className="text-[13px]" />
      Active
    </Badge>
  ) : (
    <Badge tone="neutral">
      <BanIcon className="text-[13px]" />
      Inactive
    </Badge>
  );
}
