import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { CompanyForm } from "@/components/company-form";
import { fetchCurrentUser } from "@/lib/auth";
import { getCompany } from "@/lib/company";

interface EditCompanyPageProps {
  params: Promise<{ id: string }>;
}

export default async function EditCompanyPage({ params }: EditCompanyPageProps) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");
  if (user.role !== "ADMIN") redirect("/app/companies");

  const { id } = await params;
  let company;

  try {
    company = await getCompany(id, cookieHeader || undefined);
  } catch {
    notFound();
  }

  return (
    <AppLayout user={user} title={`Edit ${company.display_name}`} description="Update company profile information.">
      <CompanyForm initial={company} />
    </AppLayout>
  );
}
