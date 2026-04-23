import { describe, it, expect } from "vitest";
import { cn, formatCurrency, formatDate } from "./utils";

describe("utils", () => {
  it("cn joins class names", () => {
    expect(cn("a", "b")).toBe("a b");
    expect(cn("a", { b: true, c: false })).toBe("a b");
  });

  it("formatCurrency formats number as USD", () => {
    // Note: Intl format might vary slightly by environment, so we check for currency symbol and digits
    const formatted = formatCurrency(123.45);
    expect(formatted).toContain("$");
    expect(formatted).toContain("123.45");
  });

  it("formatDate formats date string", () => {
    const formatted = formatDate("2024-04-23");
    // Result depends on locale, but should contain month and day
    expect(formatted).toContain("2024");
    expect(formatted).toContain("Apr");
  });
});
