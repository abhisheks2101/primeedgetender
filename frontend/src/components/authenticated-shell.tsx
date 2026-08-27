"use client";

import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { logoutRequest, type UserProfile } from "@/lib/auth";

interface AuthenticatedShellProps {
  user: UserProfile;
}

export function AuthenticatedShell({ user }: AuthenticatedShellProps) {
  const router = useRouter();

  async function handleLogout() {
    await logoutRequest();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-3xl flex-col px-6 py-12">
      <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-500">Tender Intelligence Platform</p>
          <h1 className="text-3xl font-bold tracking-tight text-slate-950">Authenticated Application Shell</h1>
        </div>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Authentication successfully configured.</CardTitle>
          <CardDescription>This protected area confirms Module 2 authentication is working.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border border-slate-100 bg-slate-50 p-4">
            <p className="text-sm text-slate-500">User</p>
            <p className="text-lg font-medium text-slate-900">{user.full_name}</p>
            <p className="text-sm text-slate-600">{user.email}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500">Role</span>
            <Badge variant={user.role === "ADMIN" ? "default" : "secondary"}>{user.role}</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
