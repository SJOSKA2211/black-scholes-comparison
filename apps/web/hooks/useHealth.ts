"use client";
import { useQuery } from "@tanstack/react-query";
import { useApi } from "./useApi";

interface HealthStatus {
  status: "ok" | "error";
  timestamp: number;
  services: {
    database: string;
    redis: string;
    rabbitmq: string;
    storage: string;
  };
}

export function useHealth() {
  const { get } = useApi();

  return useQuery({
    queryKey: ["health"],
    queryFn: () => get<HealthStatus>("/health"),
    refetchInterval: 30000, // Refresh every 30s
  });
}
