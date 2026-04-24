"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export function useAuth() {
  const [user] = useState<any>({
    id: "00000000-0000-0000-0000-000000000000",
    email: "researcher@example.com",
    user_metadata: { role: "researcher" },
  });
  const [loading] = useState(false);
  const router = useRouter();

  const signOut = async () => {
    // No-op in stripped auth mode
    router.push("/");
  };

  return { user, loading, signOut };
}
