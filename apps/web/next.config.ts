import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
