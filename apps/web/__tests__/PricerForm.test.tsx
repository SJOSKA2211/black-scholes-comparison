import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PricerForm } from "@/components/forms/PricerForm";
import { OptionParams } from "@/types";

const mockParams: OptionParams = {
  underlying_price: 100,
  strike_price: 100,
  maturity_years: 1,
  volatility: 0.2,
  risk_free_rate: 0.05,
  option_type: "call",
  is_american: false,
  market_source: "synthetic",
};

describe("PricerForm", () => {
  it("renders all parameter inputs", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);

    expect(screen.getByLabelText(/Underlying Price/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Strike Price/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Maturity/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Volatility/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Risk-Free Rate/i)).toBeInTheDocument();
  });

  it("calls setParams when input changes", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);

    const input = screen.getByLabelText(/Underlying Price/i);
    fireEvent.change(input, { target: { value: "110" } });

    expect(setParams).toHaveBeenCalledWith(
      expect.objectContaining({
        underlying_price: 110,
      }),
    );
  });

  it("calls setParams when switch is toggled", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);

    // Switch for American Option
    const switchElement = screen.getByRole("switch");
    fireEvent.click(switchElement);

    expect(setParams).toHaveBeenCalledWith(
      expect.objectContaining({
        is_american: true,
      }),
    );
  });

  it("updates maturity years correctly", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);

    const input = screen.getByLabelText(/Maturity/i);
    fireEvent.change(input, { target: { value: "2.5" } });

    expect(setParams).toHaveBeenCalledWith(
      expect.objectContaining({
        maturity_years: 2.5,
      }),
    );
  });
});
