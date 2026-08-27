import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 py-12">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-slate-950">Tender Intelligence Platform</h1>
        <p className="mt-2 text-sm text-slate-600">Sign in to access the protected application shell.</p>
      </div>
      <LoginForm />
    </main>
  );
}
