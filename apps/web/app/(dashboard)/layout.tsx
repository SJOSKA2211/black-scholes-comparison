import { createServerClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Dev bypass for E2E tests (Section 16.3)
  const skipAuth = process.env.SKIP_AUTH === "true" || process.env.NODE_ENV === "test";
  
  if (!session && !skipAuth) {
    redirect("/login");
  }

  // Mock user if skipping auth
  const user = session?.user || {
    id: "00000000-0000-0000-0000-000000000000",
    email: "test@example.com",
    user_metadata: { full_name: "Test User" },
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-50">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header user={user} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
