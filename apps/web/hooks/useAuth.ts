"use client";
import { useState } from "react";

export function useAuth() {
  const [user] = useState<any>({
    id: "00000000-0000-0000-0000-000000000000",
    email: "researcher@example.com",
    user_metadata: { role: "researcher", full_name: "Researcher" },
  });
  const [loading] = useState(false);

  const signOut = () => {
    // No-op in stripped auth mode
    console.log("Sign out requested, but auth is stripped.");
  };

  return { user, loading, signOut };
}
