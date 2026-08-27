import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AuthenticatedShell } from "@/components/authenticated-shell";
import { fetchCurrentUser } from "@/lib/auth";

export default async function AppPage() {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore.toString();
  const user = await fetchCurrentUser(cookieHeader || undefined);

  if (!user) {
    redirect("/login");
  }

  return <AuthenticatedShell user={user} />;
}
