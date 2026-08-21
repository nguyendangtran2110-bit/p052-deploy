import { describe, expect, it } from "vitest";
import { formatFileSize, label } from "@/lib/format";

describe("frontend display helpers", () => {
  it("maps backend enum values to Vietnamese labels", () => {
    expect(label("in_progress")).toBe("Đang xử lý");
    expect(label("waiting_management")).toBe("Chờ ban quản lý");
  });

  it("formats attachment sizes", () => {
    expect(formatFileSize(1024)).toBe("1 KB");
    expect(formatFileSize(2 * 1024 * 1024)).toBe("2.0 MB");
  });
});
