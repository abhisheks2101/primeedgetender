import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { listTenderDocuments } from "@/lib/tender-document";

export default async function TenderDocumentsAdminPage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  const documents = await listTenderDocuments(cookieHeader || undefined);

  return (
    <AppLayout
      user={user}
      title="Tender Documents"
      description="Download, validate, and extract text from tender documents discovered during collection."
    >
      <Card>
        <CardHeader>
          <CardTitle>Document Processing</CardTitle>
          <CardDescription>
            Module 8 prepares documents for structured information extraction in Module 9. No eligibility analysis is performed here.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Document</th>
                  <th className="px-3 py-2">Classification</th>
                  <th className="px-3 py-2">Download</th>
                  <th className="px-3 py-2">Processing</th>
                  <th className="px-3 py-2">Extraction</th>
                  <th className="px-3 py-2">Pages</th>
                  <th className="px-3 py-2">Error</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <tr key={document.id} className="border-b border-slate-100">
                    <td className="px-3 py-3">
                      <Link href={`/admin/tender-documents/${document.id}`} className="font-medium text-slate-900 hover:underline">
                        {document.document_name}
                      </Link>
                      <p className="text-xs text-slate-500">{document.source_document_id}</p>
                    </td>
                    <td className="px-3 py-3">{document.classification}</td>
                    <td className="px-3 py-3">
                      <Badge variant="secondary">{document.download_status}</Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge variant="secondary">{document.processing_status}</Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge variant="secondary">{document.extraction_status}</Badge>
                    </td>
                    <td className="px-3 py-3">{document.page_count ?? "—"}</td>
                    <td className="px-3 py-3 text-xs text-red-600">{document.error_message || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {documents.length === 0 ? <p className="py-6 text-sm text-slate-500">No tender documents discovered yet.</p> : null}
          </div>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
