import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  Select,
  SelectItem,
  SelectTrigger,
  SelectValue,
  SelectContent,
} from "@/components/ui/select";

describe("Select UI Component", () => {
  it("renders and handles selection", () => {
    const onValueChange = vi.fn();
    render(
      <Select value="val1" onValueChange={onValueChange}>
        <SelectTrigger>
          <SelectValue placeholder="Select..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="val1">Option 1</SelectItem>
          <SelectItem value="val2">Option 2</SelectItem>
        </SelectContent>
      </Select>,
    );

    expect(screen.getByText("Option 1")).toBeInTheDocument();

    const option2 = screen.getByText("Option 2");
    fireEvent.click(option2);
    expect(onValueChange).toHaveBeenCalledWith("val2");
  });

  it("covers non-element children in Select (Line 22)", () => {
    render(
      <Select>
        {"Text Child"}
        <SelectItem value="val">Item</SelectItem>
      </Select>,
    );
    expect(screen.getByText("Text Child")).toBeInTheDocument();
  });

  it("covers SelectItem without onValueChange (Line 94)", () => {
    render(<SelectItem value="val">No Callback</SelectItem>);
    const item = screen.getByText("No Callback");
    // Should not throw
    fireEvent.click(item);
  });

  it("covers SelectValue with value (Line 55)", () => {
    render(<SelectValue value="Current" placeholder="None" />);
    expect(screen.getByText("Current")).toBeInTheDocument();
  });

  it("covers SelectValue with nothing (Line 55)", () => {
    const { container } = render(<SelectValue />);
    expect(container.firstChild?.textContent).toBe("");
  });
});
