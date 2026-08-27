import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";

export default async function AppHomePage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);

  if (!user) {
    redirect("/login");
  }

  return (
    <AppLayout
      user={user}
      title="Application Home"
      description="Authentication is configured. Company profile management is available in Module 3."
    >
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Authentication successfully configured.</CardTitle>
            <CardDescription>Module 2 session and role information.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-slate-500">User</p>
              <p className="font-medium">{user.full_name}</p>
              <p className="text-sm text-slate-600">{user.email}</p>
            </div>
            <Badge variant={user.role === "ADMIN" ? "default" : "secondary"}>{user.role}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Company Profiles</CardTitle>
            <CardDescription>Manage multiple independent company profiles and supporting documents.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/app/companies">Open Companies</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
