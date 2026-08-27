import Link from "next/link";
import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { CompanyDetailTabs } from "@/components/company-detail-tabs";
import { Button } from "@/components/ui/button";
import { fetchCurrentUser } from "@/lib/auth";
import {
  getCompany,
  listCapabilities,
  listDocuments,
  listExperiences,
} from "@/lib/company";

interface CompanyDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function CompanyDetailPage({ params }: CompanyDetailPageProps) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");

  const { id } = await params;
  let company;
  let experiences;
  let capabilities;
  let documents;

  try {
    [company, experiences, capabilities, documents] = await Promise.all([
      getCompany(id, cookieHeader || undefined),
      listExperiences(id, cookieHeader || undefined),
      listCapabilities(id, cookieHeader || undefined),
      listDocuments(id, cookieHeader || undefined),
    ]);
  } catch {
    notFound();
  }

  return (
    <AppLayout
      user={user}
      title={company.display_name}
      description="Company profile overview with structured sections for future tender matching."
      actions={
        user.role === "ADMIN" ? (
          <Button asChild variant="outline">
            <Link href={`/app/companies/${company.id}/edit`}>Edit Company</Link>
          </Button>
        ) : null
      }
    >
      <CompanyDetailTabs
        company={company}
        experiences={experiences}
        capabilities={capabilities}
        documents={documents}
        isAdmin={user.role === "ADMIN"}
      />
    </AppLayout>
  );
}
