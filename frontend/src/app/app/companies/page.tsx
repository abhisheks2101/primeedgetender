import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { listCompanies } from "@/lib/company";

interface CompaniesPageProps {
  searchParams: Promise<{ search?: string; active_only?: string }>;
}

export default async function CompaniesPage({ searchParams }: CompaniesPageProps) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  const params = await searchParams;
  const activeOnly = params.active_only === "true" ? true : params.active_only === "false" ? false : undefined;
  const companies = await listCompanies(params.search, activeOnly, cookieHeader || undefined);

  return (
    <AppLayout
      user={user}
      title="Companies"
      description="Manage multiple company profiles, capabilities, experience, and supporting documents."
      actions={
        user.role === "ADMIN" ? (
          <Button asChild>
            <Link href="/app/companies/new">Create Company</Link>
          </Button>
        ) : null
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Company List</CardTitle>
          <CardDescription>Search and filter company profiles stored in the platform.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form className="flex flex-wrap gap-3">
            <input
              name="search"
              defaultValue={params.search || ""}
              placeholder="Search companies"
              className="h-10 min-w-[240px] rounded-md border border-slate-200 px-3 text-sm"
            />
            <select
              name="active_only"
              defaultValue={params.active_only || ""}
              className="h-10 rounded-md border border-slate-200 px-3 text-sm"
            >
              <option value="">All statuses</option>
              <option value="true">Active only</option>
              <option value="false">Inactive only</option>
            </select>
            <Button type="submit">Apply</Button>
          </form>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Company</th>
                  <th className="px-3 py-2">Entity Type</th>
                  <th className="px-3 py-2">Location</th>
                  <th className="px-3 py-2">Projects</th>
                  <th className="px-3 py-2">Registrations</th>
                  <th className="px-3 py-2">Documents</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={company.id} className="border-b border-slate-100">
                    <td className="px-3 py-3">
                      <Link href={`/app/companies/${company.id}`} className="font-medium text-slate-900 hover:underline">
                        {company.display_name}
                      </Link>
                      <p className="text-xs text-slate-500">{company.legal_name}</p>
                    </td>
                    <td className="px-3 py-3">{company.legal_entity_type || "—"}</td>
                    <td className="px-3 py-3">
                      {[company.city, company.state].filter(Boolean).join(", ") || "—"}
                    </td>
                    <td className="px-3 py-3">{company.project_count}</td>
                    <td className="px-3 py-3">{company.registration_count}</td>
                    <td className="px-3 py-3">{company.document_count}</td>
                    <td className="px-3 py-3">
                      <Badge variant={company.is_active ? "success" : "secondary"}>
                        {company.is_active ? "Active" : "Archived"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {companies.length === 0 ? <p className="py-6 text-sm text-slate-500">No companies found.</p> : null}
          </div>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
