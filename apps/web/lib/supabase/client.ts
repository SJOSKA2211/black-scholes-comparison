import { createBrowserClient as createSupabaseBrowserClient } from "@supabase/ssr";

let client: any = null;

export function createBrowserClient() {
  if (!client) {
    client = createSupabaseBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    );
  }
  return client;
}
