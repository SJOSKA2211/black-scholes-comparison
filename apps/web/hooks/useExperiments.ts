"use client";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "./useApi";
import { useRealtime } from "./useRealtime";
import { PaginatedResponse, Experiment } from "@/types";

interface UseExperimentsOptions {
  methodType?: string;
  marketSource?: string;
  page?: number;
  pageSize?: number;
}

export function useExperiments(options: UseExperimentsOptions = {}) {
  const { get } = useApi();
  const qc = useQueryClient();
  const { methodType, marketSource, page = 1, pageSize = 50 } = options;

  const queryKey = [
    "experiments",
    { methodType, marketSource, page, pageSize },
  ];

  const query = useQuery({
    queryKey,
    queryFn: () => {
      const params = new URLSearchParams();
      if (methodType) params.append("method_type", methodType);
      if (marketSource) params.append("market_source", marketSource);
      params.append("page", page.toString());
      params.append("page_size", pageSize.toString());

      return get<PaginatedResponse<Experiment>>(
        `/api/v1/experiments/results?${params.toString()}`,
      );
    },
  });

  // Realtime subscription for live experiment updates
  useRealtime<Experiment>({
    table: "method_results",
    event: "INSERT",
    onData: (newExperiment) => {
      qc.setQueryData<PaginatedResponse<Experiment>>(queryKey, (old) => {
        if (!old) return old;
        return {
          ...old,
          items: [newExperiment, ...old.items].slice(0, pageSize),
          total: old.total + 1,
        };
      });
    },
  });

  return {
    ...query,
    experiments: query.data?.items ?? [],
  };
}
