import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/ui/providers";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "PixelPro — AI Product Image Enhancer",
  description:
    "Transform blurry, low-res product photos into stunning, high-resolution images with AI. Boost sales with professional-quality visuals in seconds.",
  keywords: ["image enhancement", "AI upscaling", "product photography", "ecommerce images"],
  openGraph: {
    title: "PixelPro — AI Product Image Enhancer",
    description: "Turn your product photos into sales machines with AI enhancement.",
    images: ["/og-image.png"],
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased bg-white dark:bg-gray-950`}>
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
