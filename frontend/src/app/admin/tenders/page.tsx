import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { listTenders } from "@/lib/tender";

export default async function TendersAdminPage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  const tenders = await listTenders(cookieHeader || undefined);

  return (
    <AppLayout
      user={user}
      title="Normalized Tenders"
      description="Administrative view of normalized tender records from all collectors."
    >
      <Card>
        <CardHeader>
          <CardTitle>Tender List</CardTitle>
          <CardDescription>Common normalized representation regardless of UP or MP source.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Title</th>
                  <th className="px-3 py-2">Reference</th>
                  <th className="px-3 py-2">State</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Normalization</th>
                  <th className="px-3 py-2">Submission End</th>
                </tr>
              </thead>
              <tbody>
                {tenders.map((tender) => (
                  <tr key={tender.id} className="border-b border-slate-100">
                    <td className="px-3 py-3">
                      <Link href={`/admin/tenders/${tender.id}`} className="font-medium text-slate-900 hover:underline">
                        {tender.title || tender.source_tender_id}
                      </Link>
                    </td>
                    <td className="px-3 py-3">{tender.reference_number || "—"}</td>
                    <td className="px-3 py-3">{tender.state_code.replace("_", " ")}</td>
                    <td className="px-3 py-3">
                      <Badge variant="secondary">{tender.status}</Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge variant={tender.normalization_status === "NORMALIZED" ? "success" : "secondary"}>
                        {tender.normalization_status}
                      </Badge>
                    </td>
                    <td className="px-3 py-3 text-xs text-slate-600">
                      {tender.submission_end ? new Date(tender.submission_end).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {tenders.length === 0 ? <p className="py-6 text-sm text-slate-500">No normalized tenders yet.</p> : null}
          </div>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
