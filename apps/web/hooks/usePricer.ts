"use client";
import { useMutation } from "@tanstack/react-query";
import { useApi } from "./useApi";
import type { PriceRequest, PriceResponse } from "@/types";
 
/** Prices an option with all requested methods. Used in Live Pricer page.
 *  Every slider change calls mutate() — results update in < 500ms.
 */
export function usePricer() {
  const { post } = useApi();
  return useMutation({
    mutationFn: (req: PriceRequest) =>
      post<PriceResponse>("/api/v1/price", req),
  });
}
