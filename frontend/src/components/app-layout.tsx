"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { UserProfile } from "@/lib/auth";
import { logoutRequest } from "@/lib/auth";

interface AppLayoutProps {
  user: UserProfile;
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export function AppLayout({ user, title, description, children, actions }: AppLayoutProps) {
  const router = useRouter();

  async function handleLogout() {
    await logoutRequest();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8">
      <header className="mb-8 space-y-4 border-b border-slate-200 pb-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-slate-500">Tender Intelligence Platform</p>
            <h1 className="text-3xl font-bold tracking-tight text-slate-950">{title}</h1>
            {description ? <p className="mt-2 text-sm text-slate-600">{description}</p> : null}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant={user.role === "ADMIN" ? "default" : "secondary"}>{user.role}</Badge>
            <span className="text-sm text-slate-600">{user.full_name}</span>
            <Button variant="outline" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
        <nav className="flex flex-wrap gap-3 text-sm">
          <Link href="/app" className="text-slate-600 hover:text-slate-950">
            Home
          </Link>
          <Link href="/app/companies" className="text-slate-600 hover:text-slate-950">
            Companies
          </Link>
          <Link href="/admin/tender-sources" className="text-slate-600 hover:text-slate-950">
            Tender Sources
          </Link>
          <Link href="/admin/tenders" className="text-slate-600 hover:text-slate-950">
            Tenders
          </Link>
          <Link href="/admin/tender-documents" className="text-slate-600 hover:text-slate-950">
            Tender Documents
          </Link>
          {user.role === "ADMIN" ? (
            <Link href="/admin/tender-duplicates" className="text-slate-600 hover:text-slate-950">
              Duplicate Review
            </Link>
          ) : null}
        </nav>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </header>
      {children}
    </div>
  );
}
