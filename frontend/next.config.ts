import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // [>]: Enable standalone output for Docker deployment.
  // This creates a self-contained build without node_modules.
  output: "standalone",
};

export default nextConfig;
