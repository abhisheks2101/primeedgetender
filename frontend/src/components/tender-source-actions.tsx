"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { updateTenderSourceStatus } from "@/lib/tender-source";

interface TenderSourceActionsProps {
  sourceId: string;
  isActive: boolean;
}

export function TenderSourceActions({ sourceId, isActive }: TenderSourceActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function toggleActive() {
    setLoading(true);
    try {
      await updateTenderSourceStatus(sourceId, { is_active: !isActive });
      router.refresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button variant="outline" onClick={toggleActive} disabled={loading}>
      {isActive ? "Disable Source" : "Enable Source"}
    </Button>
  );
}
