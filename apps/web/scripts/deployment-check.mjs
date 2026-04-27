/**
 * Enhanced Vercel Deployment Check Script (MJS)
 * Validates required environment variables, URL formats, and configuration before build.
 */

const REQUIRED_ENV_VARS = [
  "NEXT_PUBLIC_SUPABASE_URL",
  "NEXT_PUBLIC_SUPABASE_ANON_KEY",
  "NEXT_PUBLIC_API_URL",
];

const URL_VARS = ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_API_URL"];

function checkEnvVars() {
  console.log("🔍 Running deployment checks...");
  const missing = REQUIRED_ENV_VARS.filter((v) => !process.env[v]);

  if (missing.length > 0) {
    console.error("❌ MISSING REQUIRED ENVIRONMENT VARIABLES:");
    missing.forEach((v) => console.error(`   - ${v}`));
    console.error("Please ensure these are set in the Vercel project settings.");
    process.exit(1);
  }

  console.log("✅ All required environment variables are present.");
}

function validateUrls() {
  console.log("🌐 Validating URL formats...");
  let allValid = true;

  URL_VARS.forEach((v) => {
    const url = process.env[v];
    try {
      new URL(url);
      console.log(`   ✅ ${v} is a valid URL: ${url}`);
    } catch (e) {
      console.error(`   ❌ ${v} is NOT a valid URL: ${url}`);
      allValid = false;
    }
  });

  if (!allValid) {
    console.error("Invalid URL format detected. Build aborted.");
    process.exit(1);
  }
}

async function checkReachability() {
  // Only run reachability check if explicitly enabled or in a non-Vercel environment
  // to avoid build failures due to private network isolation during Vercel builds.
  if (process.env.SKIP_REACHABILITY_CHECK === "true") {
    console.log("⏭️ Skipping reachability checks as requested.");
    return;
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  console.log(`📡 Testing API reachability: ${apiUrl}/health`);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const response = await fetch(`${apiUrl}/health`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      console.log(`   ✅ API is reachable. Status: ${data.status}`);
      if (data.status !== "ok") {
        console.warn(`   ⚠️ API reported sub-optimal health:`, data.services);
      }
    } else {
      console.warn(`   ⚠️ API returned status ${response.status}. This might cause runtime issues.`);
    }
  } catch (error) {
    if (error.name === "AbortError") {
      console.warn(`   ⚠️ API reachability test TIMED OUT after 15s.`);
      console.warn("      (This often happens if the backend is waking up from a cold start on Render)");
    } else {
      console.warn(`   ⚠️ API reachability test failed: ${error.message}`);
    }
    console.warn("      (This is non-fatal during build but verify connectivity in production)");
  }
}

async function run() {
  try {
    checkEnvVars();
    validateUrls();
    await checkReachability();
    console.log("✨ All deployment checks passed.");
  } catch (error) {
    console.error("💥 Deployment checks failed:", error);
    process.exit(1);
  }
}

run();
