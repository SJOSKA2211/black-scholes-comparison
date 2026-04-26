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
    process.exit(1);
  }
}

async function checkReachability() {
  if (process.env.SKIP_REACHABILITY_CHECK === "true") {
    console.log("⏭️ Skipping reachability checks.");
    return;
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  console.log(`📡 Testing API reachability: ${apiUrl}/health`);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${apiUrl}/health`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      console.log("   ✅ API is reachable and healthy.");
    } else {
      console.warn(`   ⚠️ API returned status ${response.status}. Deployment might be unstable.`);
    }
  } catch (error) {
    console.warn(`   ⚠️ API reachability test failed: ${error.message}`);
    console.warn("      (This is expected if the API is not yet deployed or is in a private network)");
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
