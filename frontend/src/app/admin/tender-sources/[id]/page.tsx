import Link from "next/link";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { CollectNowButton } from "@/components/collect-now-button";
import { TenderSourceActions } from "@/components/tender-source-actions";
import { TenderSourceForm } from "@/components/tender-source-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { getTenderSource, listSourceJobs } from "@/lib/tender-source";

interface TenderSourceDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function TenderSourceDetailPage({ params }: TenderSourceDetailPageProps) {
  const { id } = await params;
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  let source;
  let jobs;
  try {
    [source, jobs] = await Promise.all([
      getTenderSource(id, cookieHeader || undefined),
      listSourceJobs(id, cookieHeader || undefined),
    ]);
  } catch {
    notFound();
  }

  return (
    <AppLayout
      user={user}
      title={source.name}
      description={`Source code ${source.code} • ${source.collection_method}`}
      actions={
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/admin/tender-sources">Back to Sources</Link>
          </Button>
          {user.role === "ADMIN" ? <TenderSourceActions sourceId={source.id} isActive={source.is_active} /> : null}
          {user.role === "ADMIN" ? (
            <CollectNowButton sourceId={source.id} sourceCode={source.code} isActive={source.is_active} />
          ) : null}
        </div>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Source Information</CardTitle>
            <CardDescription>Administrative metadata and health indicators.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <span className="font-medium">Authority:</span> {source.authority || "—"}
            </p>
            <p>
              <span className="font-medium">State:</span> {source.state || "—"}
            </p>
            <p>
              <span className="font-medium">Portal URL:</span> {source.portal_url || "—"}
            </p>
            <p>
              <span className="font-medium">Source Type:</span> {source.source_type}
            </p>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-medium">Status:</span>
              <Badge variant={source.is_active ? "success" : "secondary"}>
                {source.is_active ? "Active" : "Inactive"}
              </Badge>
              <Badge variant="secondary">{source.health_status}</Badge>
            </div>
            <p>
              <span className="font-medium">Last Success:</span>{" "}
              {source.last_success_at ? new Date(source.last_success_at).toLocaleString() : "—"}
            </p>
            <p>
              <span className="font-medium">Last Error:</span> {source.last_error || "—"}
            </p>
            <p>
              <span className="font-medium">Description:</span> {source.description || "—"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Configuration Summary</CardTitle>
            <CardDescription>Safe, non-secret collection parameters.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Source URL: {source.configuration?.source_url || "—"}</p>
            <p>Search URL: {source.configuration?.search_url || "—"}</p>
            <p>Timeout: {source.configuration?.request_timeout_seconds ?? "—"}s</p>
            <p>Retry Count: {source.configuration?.retry_count ?? "—"}</p>
            <p>Request Delay: {source.configuration?.request_delay_seconds ?? "—"}s</p>
            <p>Max Requests: {source.configuration?.max_requests_per_collection ?? "—"}</p>
          </CardContent>
        </Card>
      </div>

      {user.role === "ADMIN" ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Edit Source</CardTitle>
          </CardHeader>
          <CardContent>
            <TenderSourceForm initial={source} />
          </CardContent>
        </Card>
      ) : null}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Collection History</CardTitle>
          <CardDescription>Historical collection jobs for this source. No live collection is triggered here.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Started</th>
                  <th className="px-3 py-2">Completed</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Discovered</th>
                  <th className="px-3 py-2">Processed</th>
                  <th className="px-3 py-2">Created</th>
                  <th className="px-3 py-2">Updated</th>
                  <th className="px-3 py-2">Skipped</th>
                  <th className="px-3 py-2">Failed</th>
                  <th className="px-3 py-2">Duration</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="border-b border-slate-100">
                    <td className="px-3 py-3">{job.started_at ? new Date(job.started_at).toLocaleString() : "—"}</td>
                    <td className="px-3 py-3">{job.completed_at ? new Date(job.completed_at).toLocaleString() : "—"}</td>
                    <td className="px-3 py-3">{job.status}</td>
                    <td className="px-3 py-3">{job.records_discovered}</td>
                    <td className="px-3 py-3">{job.records_processed}</td>
                    <td className="px-3 py-3">{job.records_created}</td>
                    <td className="px-3 py-3">{job.records_updated}</td>
                    <td className="px-3 py-3">{job.records_skipped}</td>
                    <td className="px-3 py-3">{job.records_failed}</td>
                    <td className="px-3 py-3">{job.duration_seconds ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {jobs.length === 0 ? <p className="py-6 text-sm text-slate-500">No collection jobs recorded yet.</p> : null}
          </div>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
