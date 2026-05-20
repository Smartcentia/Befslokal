import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true, // Temporary: NextAuth v4 type compatibility with Next.js 16
  },

  reactStrictMode: false,

  // CRITICAL: Ensure Prisma client is included in standalone build
  outputFileTracingIncludes: {
    '/api/**/*': [
      './node_modules/.prisma/**/*',
      './node_modules/@prisma/**/*',
    ],
  },
};

export default nextConfig;

