"use client";
import { useNotifications } from "@/hooks/useNotifications";
import { Bell } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

export default function NotificationBell() {
  const { notifications, unreadCount, markRead } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-400 hover:text-white transition-colors"
      >
        <Bell className="h-5 w-5" />
        <AnimatePresence>
          {unreadCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white shadow-lg"
            >
              {unreadCount}
            </motion.span>
          )}
        </AnimatePresence>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute right-0 z-50 mt-2 w-80 rounded-2xl border border-slate-800 bg-slate-900 p-2 shadow-2xl"
            >
              <div className="p-4 flex items-center justify-between">
                <h3 className="font-semibold text-white">Notifications</h3>
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  {unreadCount} UNREAD
                </span>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center text-sm text-slate-500">
                    All caught up.
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => markRead.mutate(n.id)}
                      className="group flex cursor-pointer gap-3 rounded-xl p-3 hover:bg-slate-800/50 transition-colors"
                    >
                      <div
                        className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                          n.severity === "critical"
                            ? "bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]"
                            : n.severity === "error"
                              ? "bg-orange-500"
                              : n.severity === "warning"
                                ? "bg-amber-500"
                                : "bg-blue-500"
                        }`}
                      />
                      <div>
                        <p className="text-sm font-medium text-slate-200">
                          {n.title}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">
                          {n.body}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
