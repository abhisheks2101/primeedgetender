import { formatStatusLabel } from "@/lib/api";

describe("formatStatusLabel", () => {
  it("formats snake_case statuses for display", () => {
    expect(formatStatusLabel("requires_verification")).toBe("requires verification");
    expect(formatStatusLabel("healthy")).toBe("healthy");
  });
});
