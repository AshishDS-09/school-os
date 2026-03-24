
// frontend/app/layout.tsx

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "School OS — AI-Powered School Management",
  description: "AI-powered school operating system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
