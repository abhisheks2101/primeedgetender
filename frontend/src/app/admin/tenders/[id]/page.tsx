import Link from "next/link";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { getTender } from "@/lib/tender";

interface TenderDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function TenderDetailPage({ params }: TenderDetailPageProps) {
  const { id } = await params;
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  let tender;
  try {
    tender = await getTender(id, cookieHeader || undefined);
  } catch {
    notFound();
  }

  return (
    <AppLayout
      user={user}
      title={tender.title || tender.source_tender_id}
      description="Normalized tender detail with source metadata preserved."
      actions={
        <Button asChild variant="outline">
          <Link href="/admin/tenders">Back to Tenders</Link>
        </Button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Common normalized fields</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <span className="text-slate-500">Source tender ID:</span> {tender.source_tender_id}
            </p>
            <p>
              <span className="text-slate-500">Reference:</span> {tender.reference_number || "—"}
            </p>
            <p>
              <span className="text-slate-500">Organization:</span> {tender.organization || "—"}
            </p>
            <p>
              <span className="text-slate-500">Location:</span> {tender.location || tender.original_location_text || "—"}
            </p>
            <p>
              <span className="text-slate-500">State:</span> {tender.state_code.replace("_", " ")}
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <Badge variant="secondary">{tender.status}</Badge>
              <Badge variant={tender.normalization_status === "NORMALIZED" ? "success" : "secondary"}>
                {tender.normalization_status}
              </Badge>
              <Badge variant="secondary">v{tender.normalization_version}</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Normalization Metadata</CardTitle>
            <CardDescription>Processing status and validation warnings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <span className="text-slate-500">Source status:</span> {tender.source_status || "—"}
            </p>
            <p>
              <span className="text-slate-500">First seen:</span>{" "}
              {tender.first_seen_at ? new Date(tender.first_seen_at).toLocaleString() : "—"}
            </p>
            <p>
              <span className="text-slate-500">Last seen:</span>{" "}
              {tender.last_seen_at ? new Date(tender.last_seen_at).toLocaleString() : "—"}
            </p>
            <p>
              <span className="text-slate-500">Normalized at:</span>{" "}
              {tender.normalized_at ? new Date(tender.normalized_at).toLocaleString() : "—"}
            </p>
            {tender.validation_warnings?.length ? (
              <ul className="list-disc pl-5 text-amber-700">
                {tender.validation_warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500">No validation warnings.</p>
            )}
            {tender.source_url ? (
              <a href={tender.source_url} className="text-blue-600 hover:underline" target="_blank" rel="noreferrer">
                View source URL
              </a>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
