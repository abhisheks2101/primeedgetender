import { Activity, Database, Server } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  formatStatusLabel,
  type ComponentStatus,
  type HealthStatus,
  type SystemStatusView,
} from "@/lib/api";

interface StatusRowProps {
  label: string;
  status: ComponentStatus | HealthStatus | "unknown";
  detail?: string;
}

function statusVariant(status: ComponentStatus | HealthStatus | "unknown") {
  if (status === "connected" || status === "healthy") return "success" as const;
  if (status === "degraded" || status === "unknown") return "warning" as const;
  return "destructive" as const;
}

function StatusRow({ label, status, detail }: StatusRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 p-4">
      <div>
        <p className="font-medium text-slate-900">{label}</p>
        {detail ? <p className="mt-1 text-sm text-slate-500">{detail}</p> : null}
      </div>
      <Badge variant={statusVariant(status)} className="capitalize">
        {formatStatusLabel(status)}
      </Badge>
    </div>
  );
}

interface SystemStatusPanelProps {
  status: SystemStatusView;
}

export function SystemStatusPanel({ status }: SystemStatusPanelProps) {
  const databaseDetail =
    status.database === "connected" && status.databaseLatencyMs != null
      ? `Latency: ${status.databaseLatencyMs} ms`
      : status.error;

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-slate-700" />
          <CardTitle>System Status</CardTitle>
        </div>
        <CardDescription>Live health information from the backend API and PostgreSQL.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <StatusRow
          label="Backend"
          status={status.backend}
          detail={
            status.backend === "connected"
              ? `Version ${status.version ?? "unknown"} · ${status.environment ?? "unknown"}`
              : status.error
          }
        />
        <StatusRow label="Database" status={status.database} detail={databaseDetail} />
        <StatusRow label="Overall" status={status.overall} />
      </CardContent>
    </Card>
  );
}

export function PlatformHeader() {
  return (
    <header className="mb-8 text-center">
      <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-600 shadow-sm">
        <Server className="h-4 w-4" />
        Module 1 · Project Foundation
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-slate-950">Tender Intelligence Platform</h1>
      <p className="mx-auto mt-3 max-w-2xl text-base text-slate-600">
        Local-first foundation for discovering and evaluating government tenders from Uttar Pradesh and
        Madhya Pradesh.
      </p>
      <div className="mt-4 inline-flex items-center gap-2 text-sm text-slate-500">
        <Database className="h-4 w-4" />
        Open-source stack · ₹0 paid services
      </div>
    </header>
  );
}
