"use client";
import { useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRealtime } from "./useRealtime";
import { useApi } from "./useApi";
import { useAuth } from "./useAuth";
import { toast } from "sonner";
import type { Notification } from "@/types";

export function useNotifications() {
  const { user } = useAuth();
  const { get, post } = useApi();
  const qc = useQueryClient();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () =>
      get<Notification[]>("/api/v1/notifications?unread_only=true"),
    enabled: !!user,
  });

  // Supabase Realtime: new notifications arrive without polling
  const onData = useCallback(
    (n: Notification) => {
      toast(n.title, { description: n.body });
      qc.setQueryData<Notification[]>(["notifications", "unread"], (old) => [
        n,
        ...(old ?? []),
      ]);
    },
    [qc],
  );

  useRealtime<Notification>({
    table: "notifications",
    event: "INSERT",
    filter: undefined,
    onData,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => post(`/api/v1/notifications/${id}/read`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return {
    notifications,
    unreadCount: notifications.filter((n) => !n.read).length,
    markRead,
  };
}
