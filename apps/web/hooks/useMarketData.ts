"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "./useApi";
import { useRealtime } from "./useRealtime";
import { MarketData } from "@/types";

interface UseMarketDataOptions {
  source: "spy" | "nse";
  fromDate?: string;
  toDate?: string;
}

export function useMarketData({
  source,
  fromDate,
  toDate,
}: UseMarketDataOptions) {
  const { get } = useApi();
  const qc = useQueryClient();

  const queryKey = ["market-data", { source, fromDate, toDate }];

  const query = useQuery({
    queryKey,
    queryFn: () => {
      const params = new URLSearchParams();
      if (fromDate) params.append("from", fromDate);
      if (toDate) params.append("to", toDate);

      params.append("source", source);
      return get<{ items: MarketData[]; total: number }>(
        `/api/v1/market-data?${params.toString()}`,
      );
    },
  });

  // Realtime subscription for live market data updates
  useRealtime<MarketData>({
    table: "market_data",
    event: "INSERT",
    onData: (newData) => {
      if (newData.data_source === source) {
        qc.setQueryData<{ items: MarketData[]; total: number }>(
          queryKey,
          (old) => {
            if (!old) return old;
            return {
              ...old,
              items: [newData, ...old.items],
              total: old.total + 1,
            };
          },
        );
      }
    },
  });

  return {
    ...query,
    data: query.data?.items ?? [],
  };
}
