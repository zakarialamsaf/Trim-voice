/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",

  // Image optimization
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "minio" },
      { protocol: "https", hostname: "*.amazonaws.com" },
      { protocol: "https", hostname: "*.s3.amazonaws.com" },
      { protocol: "https", hostname: "*.cloudfront.net" },
    ],
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },

  // Expose public env vars to the browser
  env: {
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },

  // Security headers for production
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },

  // Redirects
  async redirects() {
    return [
      { source: "/app", destination: "/enhance", permanent: false },
      { source: "/dashboard", destination: "/account", permanent: false },
    ];
  },

  // Compress output
  compress: true,
  poweredByHeader: false,

  // Webpack bundle analysis (set ANALYZE=true to use)
  ...(process.env.ANALYZE === "true"
    ? {
        experimental: {
          bundleAnalyzer: { enabled: true },
        },
      }
    : {}),
};

export default nextConfig;
