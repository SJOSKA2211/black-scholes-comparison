"use client";
import { useState } from "react";

export function useAuth() {
  const [user] = useState<any>({
    id: "a24fb1a2-700a-4590-8d43-2930596a14f2",
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
