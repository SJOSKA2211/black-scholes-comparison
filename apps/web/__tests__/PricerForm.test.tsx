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

  it("updates strike price correctly", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);
    const input = screen.getByLabelText(/Strike Price/i);
    fireEvent.change(input, { target: { value: "120" } });
    expect(setParams).toHaveBeenCalledWith(expect.objectContaining({ strike_price: 120 }));
  });

  it("updates volatility correctly", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);
    const input = screen.getByLabelText(/Volatility/i);
    fireEvent.change(input, { target: { value: "0.3" } });
    expect(setParams).toHaveBeenCalledWith(expect.objectContaining({ volatility: 0.3 }));
  });

  it("updates risk-free rate correctly", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);
    const input = screen.getByLabelText(/Risk-Free Rate/i);
    fireEvent.change(input, { target: { value: "0.06" } });
    expect(setParams).toHaveBeenCalledWith(expect.objectContaining({ risk_free_rate: 0.06 }));
  });

  it("updates option type via select", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);
    const item = screen.getByText("Put");
    fireEvent.click(item);
    expect(setParams).toHaveBeenCalledWith(expect.objectContaining({ option_type: "put" }));
  });

  it("updates market source via select", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);
    const item = screen.getByText("SPY (Live)");
    fireEvent.click(item);
    expect(setParams).toHaveBeenCalledWith(expect.objectContaining({ market_source: "spy" }));
  });

  it("updates maturity years correctly", () => {
    const setParams = vi.fn();
    render(<PricerForm params={mockParams} setParams={setParams} />);
    const input = screen.getByLabelText(/Maturity/i);
    fireEvent.change(input, { target: { value: "2.5" } });
    expect(setParams).toHaveBeenCalledWith(expect.objectContaining({ maturity_years: 2.5 }));
  });
});
