// frontend/next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output for smaller Docker images (if needed later)
  output: 'standalone',

  // Disable telemetry in production
  experimental: {
    optimizeCss: true,
  },

  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'atmqydbwbjukhagqqguy.supabase.co',
      },
    ],
    formats: ['image/webp'],
  },

  // Redirect www to non-www
  async redirects() {
    return [
      {
        source: '/',
        destination: '/login',
        permanent: false,
      },
    ];
  },
};

module.exports = nextConfig;
