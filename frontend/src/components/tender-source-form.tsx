"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createTenderSource,
  type CollectionMethod,
  type TenderSource,
  type TenderSourceInput,
  type TenderSourceType,
  updateTenderSource,
} from "@/lib/tender-source";

interface TenderSourceFormProps {
  initial?: TenderSource;
}

const sourceTypes: TenderSourceType[] = ["GOVERNMENT_PORTAL", "API", "PUBLIC_DATA", "OTHER"];
const collectionMethods: CollectionMethod[] = ["HTTP", "API", "HTML", "DOCUMENT", "OTHER"];

export function TenderSourceForm({ initial }: TenderSourceFormProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData(event.currentTarget);
    const payload: TenderSourceInput = {
      name: String(formData.get("name") || ""),
      code: String(formData.get("code") || "").toUpperCase(),
      state: String(formData.get("state") || "") || null,
      authority: String(formData.get("authority") || "") || null,
      portal_url: String(formData.get("portal_url") || "") || null,
      source_type: formData.get("source_type") as TenderSourceType,
      collection_method: formData.get("collection_method") as CollectionMethod,
      priority: Number(formData.get("priority") || 100),
      description: String(formData.get("description") || "") || null,
      is_active: formData.get("is_active") === "on",
      configuration: {
        source_url: String(formData.get("source_url") || "") || null,
        search_url: String(formData.get("search_url") || "") || null,
        request_timeout_seconds: Number(formData.get("request_timeout_seconds") || 30),
        retry_count: Number(formData.get("retry_count") || 3),
        request_delay_seconds: Number(formData.get("request_delay_seconds") || 1),
        max_requests_per_collection: Number(formData.get("max_requests_per_collection") || 100),
      },
    };

    try {
      const result = initial
        ? await updateTenderSource(initial.id, payload)
        : await createTenderSource(payload);
      router.push(`/admin/tender-sources/${result.id}`);
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to save tender source.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="name">Source Name</Label>
          <Input id="name" name="name" defaultValue={initial?.name || ""} required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="code">Source Code</Label>
          <Input
            id="code"
            name="code"
            defaultValue={initial?.code || ""}
            pattern="[A-Z0-9_]+"
            required
            disabled={Boolean(initial)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State</Label>
          <Input id="state" name="state" defaultValue={initial?.state || ""} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="authority">Authority</Label>
          <Input id="authority" name="authority" defaultValue={initial?.authority || ""} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="portal_url">Portal URL</Label>
          <Input id="portal_url" name="portal_url" type="url" defaultValue={initial?.portal_url || ""} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="priority">Priority</Label>
          <Input id="priority" name="priority" type="number" min={0} defaultValue={initial?.priority ?? 100} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="source_type">Source Type</Label>
          <select
            id="source_type"
            name="source_type"
            defaultValue={initial?.source_type || "GOVERNMENT_PORTAL"}
            className="h-10 w-full rounded-md border border-slate-200 px-3 text-sm"
          >
            {sourceTypes.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="collection_method">Collection Method</Label>
          <select
            id="collection_method"
            name="collection_method"
            defaultValue={initial?.collection_method || "HTML"}
            className="h-10 w-full rounded-md border border-slate-200 px-3 text-sm"
          >
            {collectionMethods.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <textarea
          id="description"
          name="description"
          defaultValue={initial?.description || ""}
          className="min-h-24 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="source_url">Configuration Source URL</Label>
          <Input
            id="source_url"
            name="source_url"
            type="url"
            defaultValue={initial?.configuration?.source_url || ""}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="search_url">Search URL</Label>
          <Input id="search_url" name="search_url" type="url" defaultValue={initial?.configuration?.search_url || ""} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="request_timeout_seconds">Request Timeout (seconds)</Label>
          <Input
            id="request_timeout_seconds"
            name="request_timeout_seconds"
            type="number"
            min={1}
            defaultValue={initial?.configuration?.request_timeout_seconds ?? 30}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="retry_count">Retry Count</Label>
          <Input
            id="retry_count"
            name="retry_count"
            type="number"
            min={0}
            defaultValue={initial?.configuration?.retry_count ?? 3}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="request_delay_seconds">Request Delay (seconds)</Label>
          <Input
            id="request_delay_seconds"
            name="request_delay_seconds"
            type="number"
            min={0}
            step="0.1"
            defaultValue={initial?.configuration?.request_delay_seconds ?? 1}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="max_requests_per_collection">Max Requests Per Collection</Label>
          <Input
            id="max_requests_per_collection"
            name="max_requests_per_collection"
            type="number"
            min={1}
            defaultValue={initial?.configuration?.max_requests_per_collection ?? 100}
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" name="is_active" defaultChecked={initial?.is_active ?? true} />
        Active source
      </label>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <Button type="submit" disabled={submitting}>
        {initial ? "Save Changes" : "Create Source"}
      </Button>
    </form>
  );
}
