"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRealtime } from "./useRealtime";
import { useApi } from "./useApi";
import type { Notification } from "@/types";

export function useNotifications() {
  const { get, post } = useApi();
  const queryClient = useQueryClient();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => get<Notification[]>("/api/v1/notifications?unread_only=true"),
  });

  // Realtime: new notifications arrive instantly without polling
  useRealtime<Notification>({
    table: "notifications",
    event: "INSERT",
    // filter: user ? `user_id=eq.${user.id}` : undefined,
    onData: (newNotif) => {
      queryClient.setQueryData<Notification[]>(
        ["notifications", "unread"],
        (old = []) => [newNotif, ...old]
      );
    },
  });

  const markRead = useMutation({
    mutationFn: (id: string) => post(`/api/v1/notifications/${id}/read`, {}),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const unreadCount = notifications.filter(n => !n.read).length;

  return { notifications, unreadCount, markRead };
}
