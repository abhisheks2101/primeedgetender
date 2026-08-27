import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";
import { listTenderSources } from "@/lib/tender-source";

export default async function TenderSourcesAdminPage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  const sources = await listTenderSources(cookieHeader || undefined);

  return (
    <AppLayout
      user={user}
      title="Tender Sources"
      description="Administrative view of configured tender sources and collection health."
      actions={
        user.role === "ADMIN" ? (
          <Button asChild>
            <Link href="/admin/tender-sources/new">Create Source</Link>
          </Button>
        ) : null
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Source List</CardTitle>
          <CardDescription>
            Generic source configuration for future UP and MP collectors. Actual collection is not triggered here.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Source</th>
                  <th className="px-3 py-2">State</th>
                  <th className="px-3 py-2">Authority</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Active</th>
                  <th className="px-3 py-2">Health</th>
                  <th className="px-3 py-2">Last Success</th>
                  <th className="px-3 py-2">Last Failure</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr key={source.id} className="border-b border-slate-100">
                    <td className="px-3 py-3">
                      <Link
                        href={`/admin/tender-sources/${source.id}`}
                        className="font-medium text-slate-900 hover:underline"
                      >
                        {source.name}
                      </Link>
                      <p className="text-xs text-slate-500">{source.code}</p>
                    </td>
                    <td className="px-3 py-3">{source.state || "—"}</td>
                    <td className="px-3 py-3">{source.authority || "—"}</td>
                    <td className="px-3 py-3">{source.source_type}</td>
                    <td className="px-3 py-3">
                      <Badge variant={source.is_active ? "success" : "secondary"}>
                        {source.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </td>
                    <td className="px-3 py-3">
                      <Badge variant={source.health_status === "HEALTHY" ? "success" : "secondary"}>
                        {source.health_status}
                      </Badge>
                    </td>
                    <td className="px-3 py-3 text-xs text-slate-600">
                      {source.last_success_at ? new Date(source.last_success_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-3 py-3 text-xs text-slate-600">
                      {source.last_failure_at ? new Date(source.last_failure_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {sources.length === 0 ? <p className="py-6 text-sm text-slate-500">No tender sources configured.</p> : null}
          </div>
        </CardContent>
      </Card>
    </AppLayout>
  );
}
