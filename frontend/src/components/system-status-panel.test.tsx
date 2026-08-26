import { render, screen } from "@testing-library/react";

import { SystemStatusPanel } from "@/components/system-status-panel";

describe("SystemStatusPanel", () => {
  it("renders backend and database status rows", () => {
    render(
      <SystemStatusPanel
        status={{
          backend: "connected",
          database: "connected",
          overall: "healthy",
          version: "0.1.0",
          environment: "development",
          databaseLatencyMs: 12.5,
        }}
      />,
    );

    expect(screen.getByText("System Status")).toBeInTheDocument();
    expect(screen.getByText("Backend")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getAllByText("connected")).toHaveLength(2);
    expect(screen.getByText("healthy")).toBeInTheDocument();
  });
});
