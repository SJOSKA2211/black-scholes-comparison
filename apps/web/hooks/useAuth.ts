"use client";
import { useEffect, useState } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import { User } from "@supabase/supabase-js";
import { useRouter } from "next/navigation";

export function useAuth() {
  const [user, setUser] = useState<any>({
    id: "00000000-0000-0000-0000-000000000000",
    email: "researcher@example.com",
    user_metadata: { role: "researcher" },
  });
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const signOut = async () => {
    // No-op in stripped auth mode
    router.push("/");
  };

  return { user, loading, signOut };
}
