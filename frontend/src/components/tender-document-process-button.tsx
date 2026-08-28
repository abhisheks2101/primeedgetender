"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { processTenderDocument } from "@/lib/tender-document";

interface TenderDocumentProcessButtonProps {
  documentId: string;
  label?: string;
  force?: boolean;
}

export function TenderDocumentProcessButton({ documentId, label = "Process", force = false }: TenderDocumentProcessButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleProcess() {
    setLoading(true);
    setError(null);
    try {
      await processTenderDocument(documentId, force);
      router.refresh();
    } catch (processError) {
      setError(processError instanceof Error ? processError.message : "Processing failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-1">
      <Button size="sm" disabled={loading} onClick={handleProcess}>
        {loading ? "Processing..." : label}
      </Button>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
