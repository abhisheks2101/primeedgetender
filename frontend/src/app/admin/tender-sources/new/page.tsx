import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { TenderSourceForm } from "@/components/tender-source-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCurrentUser } from "@/lib/auth";

export default async function NewTenderSourcePage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");
  if (user.role !== "ADMIN") redirect("/admin/tender-sources");

  return (
    <AppLayout
      user={user}
      title="Create Tender Source"
      description="Configure a fictional or future tender source without triggering collection."
      actions={
        <Button asChild variant="outline">
          <Link href="/admin/tender-sources">Back to Sources</Link>
        </Button>
      }
    >
      <Card>
        <CardHeader>
          <CardTitle>Source Configuration</CardTitle>
          <CardDescription>Use unique source codes such as TEST_SOURCE_A. Do not store secrets here.</CardDescription>
        </CardHeader>
        <CardContent>
          <TenderSourceForm />
        </CardContent>
      </Card>
    </AppLayout>
  );
}
