import { createServerClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Auth stripped mode: always provide a default researcher user
  const user = {
    id: "00000000-0000-0000-0000-000000000000",
    email: "researcher@example.com",
    user_metadata: { full_name: "Researcher" },
  } as any;

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
