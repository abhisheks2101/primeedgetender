"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { collectTenderSource, getCollectionJob, type CollectionJobSummary } from "@/lib/tender-source";

interface CollectNowButtonProps {
  sourceId: string;
  sourceCode: string;
  isActive: boolean;
}

export function CollectNowButton({ sourceId, sourceCode, isActive }: CollectNowButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [job, setJob] = useState<CollectionJobSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canCollect = isActive && (sourceCode === "UP_TENDER" || sourceCode.startsWith("TEST_"));

  useEffect(() => {
    if (!job || ["COMPLETED", "PARTIAL", "FAILED", "CANCELLED"].includes(job.status)) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const latest = await getCollectionJob(job.id);
        setJob(latest);
        if (["COMPLETED", "PARTIAL", "FAILED", "CANCELLED"].includes(latest.status)) {
          router.refresh();
        }
      } catch {
        // Ignore transient polling errors.
      }
    }, 2000);

    return () => window.clearInterval(interval);
  }, [job, router]);

  async function handleCollect() {
    setLoading(true);
    setError(null);
    try {
      const startedJob = await collectTenderSource(sourceId);
      setJob(startedJob);
    } catch (collectError) {
      setError(collectError instanceof Error ? collectError.message : "Collection failed to start.");
    } finally {
      setLoading(false);
    }
  }

  if (!canCollect) {
    return null;
  }

  return (
    <div className="space-y-2">
      <Button onClick={handleCollect} disabled={loading || (job !== null && job.status === "RUNNING")}>
        {loading || job?.status === "RUNNING" ? "Collecting..." : "Collect Now"}
      </Button>
      {job ? (
        <p className="text-sm text-slate-600">
          Latest job: {job.status} • discovered {job.records_discovered} • created {job.records_created} • updated{" "}
          {job.records_updated} • failed {job.records_failed}
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
