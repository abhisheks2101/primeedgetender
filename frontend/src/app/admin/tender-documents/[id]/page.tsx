import Link from "next/link";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { TenderDocumentProcessButton } from "@/components/tender-document-process-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { getTenderDocument } from "@/lib/tender-document";

interface TenderDocumentDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function TenderDocumentDetailPage({ params }: TenderDocumentDetailPageProps) {
  const { id } = await params;
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  let document;
  try {
    document = await getTenderDocument(id, cookieHeader || undefined);
  } catch {
    notFound();
  }

  return (
    <AppLayout
      user={user}
      title={document.document_name}
      description="Document metadata, extraction status, and page-level text."
      actions={
        <Button asChild variant="outline">
          <Link href="/admin/tender-documents">Back to Documents</Link>
        </Button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>File Metadata</CardTitle>
            <CardDescription>Traceability for Module 9 extraction</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <span className="text-slate-500">Tender ID:</span> {document.tender_id}
            </p>
            <p>
              <span className="text-slate-500">Checksum:</span> {document.checksum || "—"}
            </p>
            <p>
              <span className="text-slate-500">MIME type:</span> {document.mime_type || "—"}
            </p>
            <p>
              <span className="text-slate-500">Size:</span> {document.file_size ?? "—"} bytes
            </p>
            <p>
              <span className="text-slate-500">Extraction method:</span> {document.extraction_method}
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <Badge variant="secondary">{document.download_status}</Badge>
              <Badge variant="secondary">{document.processing_status}</Badge>
              <Badge variant="secondary">{document.extraction_status}</Badge>
            </div>
            {document.document_url ? (
              <a href={document.document_url} className="text-blue-600 hover:underline" target="_blank" rel="noreferrer">
                Source URL
              </a>
            ) : null}
            {user.role === "ADMIN" ? (
              <div className="flex gap-2 pt-3">
                <TenderDocumentProcessButton documentId={document.id} />
                <TenderDocumentProcessButton documentId={document.id} label="Reprocess" force />
              </div>
            ) : null}
            {document.error_message ? <p className="text-red-600">{document.error_message}</p> : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Extracted Text</CardTitle>
            <CardDescription>Page-level text without AI interpretation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {document.pages.length === 0 ? <p className="text-sm text-slate-500">No extracted text yet.</p> : null}
            {document.pages.map((page) => (
              <div key={page.id} className="rounded-md border border-slate-200 p-3">
                <p className="mb-2 text-xs font-medium text-slate-500">
                  Page {page.page_number} · {page.extraction_method}
                </p>
                <pre className="whitespace-pre-wrap text-sm text-slate-800">{page.text || "(empty)"}</pre>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
