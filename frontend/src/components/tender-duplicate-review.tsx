"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { reviewTenderDuplicate, type DuplicateReviewStatus } from "@/lib/tender";

interface TenderDuplicateReviewActionsProps {
  candidateId: string;
  currentStatus: DuplicateReviewStatus;
}

export function TenderDuplicateReviewActions({ candidateId, currentStatus }: TenderDuplicateReviewActionsProps) {
  const router = useRouter();
  const [status, setStatus] = useState(currentStatus);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleReview(nextStatus: DuplicateReviewStatus) {
    setLoading(true);
    setError(null);
    try {
      const updated = await reviewTenderDuplicate(candidateId, nextStatus);
      setStatus(updated.review_status);
      router.refresh();
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : "Review failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={status === "CONFIRMED_DUPLICATE" ? "default" : "outline"}
          disabled={loading}
          onClick={() => handleReview("CONFIRMED_DUPLICATE")}
        >
          Confirm Duplicate
        </Button>
        <Button
          size="sm"
          variant={status === "NOT_DUPLICATE" ? "default" : "outline"}
          disabled={loading}
          onClick={() => handleReview("NOT_DUPLICATE")}
        >
          Not Duplicate
        </Button>
        <Button
          size="sm"
          variant={status === "IGNORED" ? "default" : "outline"}
          disabled={loading}
          onClick={() => handleReview("IGNORED")}
        >
          Ignore
        </Button>
      </div>
      <p className="text-xs text-slate-500">Current status: {status}</p>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
