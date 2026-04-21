import { createServerClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");

  if (code) {
    const supabase = await createServerClient();
    // Exchange the auth code for a session, which handles cookie setting automatically
    await supabase.auth.exchangeCodeForSession(code);
  }

  // URL to redirect to after sign in process completes
  // This matches the login page's redirect expectations
  return NextResponse.redirect(new URL("/", request.url));
}
