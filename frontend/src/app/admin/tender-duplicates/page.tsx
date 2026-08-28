import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { TenderDuplicateReviewActions } from "@/components/tender-duplicate-review";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { listTenderDuplicates } from "@/lib/tender";

export default async function TenderDuplicatesAdminPage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");
  if (user.role !== "ADMIN") redirect("/admin/tenders");

  const candidates = await listTenderDuplicates(cookieHeader || undefined);

  return (
    <AppLayout
      user={user}
      title="Duplicate Candidates"
      description="Review potential duplicate tenders. Uncertain matches are never merged automatically."
    >
      <Card>
        <CardHeader>
          <CardTitle>Pending and Reviewed Candidates</CardTitle>
          <CardDescription>Cross-source matches are conservative and require human review.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {candidates.map((candidate) => (
            <div key={candidate.id} className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Badge variant="secondary">{candidate.match_type}</Badge>
                <Badge variant="secondary">{(candidate.confidence * 100).toFixed(1)}% confidence</Badge>
                <Badge variant={candidate.review_status === "PENDING" ? "secondary" : "success"}>
                  {candidate.review_status}
                </Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-md bg-slate-50 p-3 text-sm">
                  <p className="font-medium text-slate-900">Original tender</p>
                  <p>{candidate.tender?.title || candidate.tender_id}</p>
                  <p className="text-xs text-slate-500">
                    {candidate.tender?.state_code?.replace("_", " ")} · {candidate.tender?.source_tender_id}
                  </p>
                </div>
                <div className="rounded-md bg-slate-50 p-3 text-sm">
                  <p className="font-medium text-slate-900">Candidate duplicate</p>
                  <p>{candidate.candidate_tender?.title || candidate.candidate_tender_id}</p>
                  <p className="text-xs text-slate-500">
                    {candidate.candidate_tender?.state_code?.replace("_", " ")} ·{" "}
                    {candidate.candidate_tender?.source_tender_id}
                  </p>
                </div>
              </div>
              {candidate.matched_fields?.length ? (
                <p className="mt-3 text-xs text-slate-500">Matched fields: {candidate.matched_fields.join(", ")}</p>
              ) : null}
              <div className="mt-4">
                <TenderDuplicateReviewActions candidateId={candidate.id} currentStatus={candidate.review_status} />
              </div>
            </div>
          ))}
          {candidates.length === 0 ? <p className="text-sm text-slate-500">No duplicate candidates found.</p> : null}
        </CardContent>
      </Card>
    </AppLayout>
  );
}
