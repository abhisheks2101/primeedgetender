import { PlatformHeader, SystemStatusPanel } from "@/components/system-status-panel";
import { fetchHealthStatus } from "@/lib/api";

export default async function Home() {
  const systemStatus = await fetchHealthStatus();

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-6 py-12">
      <PlatformHeader />
      <SystemStatusPanel status={systemStatus} />
    </main>
  );
}
