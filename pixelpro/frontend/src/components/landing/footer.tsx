"use client";
import Link from "next/link";
import { Sparkles, Twitter, Github, Linkedin, Mail } from "lucide-react";

const LINKS = [
  {
    title: "Product",
    links: [
      { label: "AI Enhance", href: "/enhance" },
      { label: "AI Edit", href: "/enhance" },
      { label: "Nano Banana", href: "/enhance" },
      { label: "Batch Processing", href: "/enhance" },
      { label: "API Docs", href: "/docs" },
      { label: "Changelog", href: "#" },
    ],
  },
  {
    title: "Integrations",
    links: [
      { label: "Shopify App", href: "#" },
      { label: "WooCommerce", href: "#" },
      { label: "Amazon Seller", href: "#" },
      { label: "REST API", href: "/docs" },
      { label: "Zapier", href: "#" },
      { label: "Make / Integromat", href: "#" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "#" },
      { label: "Blog", href: "#" },
      { label: "Careers", href: "#" },
      { label: "Press Kit", href: "#" },
      { label: "Affiliate Program", href: "#" },
      { label: "Contact", href: "mailto:hello@pixelpro.ai" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
      { label: "GDPR", href: "#" },
      { label: "Security", href: "#" },
      { label: "Cookie Policy", href: "#" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="bg-gray-950 text-gray-400">
      {/* Newsletter bar */}
      <div className="border-b border-gray-800">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 py-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-white font-bold text-lg">Stay in the loop</h3>
            <p className="text-sm text-gray-400 mt-1">Product updates, AI tips, and ecommerce growth tactics.</p>
          </div>
          <form className="flex w-full max-w-sm gap-2" onSubmit={(e) => e.preventDefault()}>
            <input
              type="email"
              placeholder="you@yourshop.com"
              className="flex-1 rounded-lg border border-gray-700 bg-gray-900 px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 transition-colors flex-shrink-0">
              Subscribe
            </button>
          </form>
        </div>
      </div>

      {/* Main footer grid */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-8">
          {/* Brand column */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2 font-extrabold text-xl text-white mb-4">
              <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              PixelPro
            </Link>
            <p className="text-sm leading-relaxed text-gray-400 max-w-xs">
              AI-powered image enhancement for ecommerce sellers who want to compete on quality — not budget.
            </p>

            {/* Social */}
            <div className="flex items-center gap-3 mt-6">
              {[
                { icon: Twitter, href: "#", label: "Twitter" },
                { icon: Github, href: "#", label: "GitHub" },
                { icon: Linkedin, href: "#", label: "LinkedIn" },
                { icon: Mail, href: "mailto:hello@pixelpro.ai", label: "Email" },
              ].map(({ icon: Icon, href, label }) => (
                <Link key={label} href={href} aria-label={label}
                  className="h-9 w-9 rounded-lg border border-gray-800 bg-gray-900 flex items-center justify-center text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
                >
                  <Icon className="h-4 w-4" />
                </Link>
              ))}
            </div>

            {/* Status */}
            <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-green-900 bg-green-950 px-3 py-1">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-medium text-green-400">All systems operational</span>
            </div>
          </div>

          {/* Link columns */}
          {LINKS.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-semibold text-white uppercase tracking-widest mb-4">{col.title}</h4>
              <ul className="space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link href={link.href} className="text-sm hover:text-white transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-800 mt-14 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-500">
          <p>© 2026 PixelPro Inc. All rights reserved.</p>
          <p>Built with Real-ESRGAN · GFPGAN · FLUX.1 · FastAPI · Next.js</p>
          <div className="flex items-center gap-4">
            <Link href="#" className="hover:text-gray-300 transition-colors">Privacy</Link>
            <Link href="#" className="hover:text-gray-300 transition-colors">Terms</Link>
            <Link href="#" className="hover:text-gray-300 transition-colors">Cookies</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
