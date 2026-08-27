import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AppLayout } from "@/components/app-layout";
import { CompanyForm } from "@/components/company-form";
import { fetchCurrentUser } from "@/lib/auth";

export default async function NewCompanyPage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);
  if (!user) redirect("/login");
  if (user.role !== "ADMIN") redirect("/app/companies");

  return (
    <AppLayout user={user} title="Create Company" description="Add a new company profile to the platform.">
      <CompanyForm />
    </AppLayout>
  );
}
