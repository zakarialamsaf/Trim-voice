"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Sparkles, Menu, X, ChevronDown, Zap, Image, Wand2, BarChart3 } from "lucide-react";

const products = [
  { icon: Zap, label: "AI Enhance", desc: "4K upscaling & denoising", href: "/enhance" },
  { icon: Wand2, label: "AI Edit", desc: "Instruction-following edits", href: "/enhance" },
  { icon: Image, label: "Nano Banana", desc: "Viral style transforms", href: "/enhance" },
  { icon: BarChart3, label: "Batch Processing", desc: "Process 100s at once", href: "/enhance" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [productOpen, setProductOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <>
      {/* Announcement Bar */}
      <div className="bg-gradient-to-r from-brand-600 via-purple-600 to-brand-700 text-white text-center py-2 px-4 text-sm font-medium">
        🎉 <strong>3 days free</strong> — full Pro access, no card needed. Then just $10/month. &nbsp;
        <Link href="/enhance" className="underline underline-offset-2 hover:text-brand-200 transition-colors font-semibold">
          Try it free →
        </Link>
      </div>

      <nav className={`sticky top-0 z-50 transition-all duration-200 ${scrolled ? "bg-white/95 backdrop-blur-md shadow-sm border-b border-gray-200" : "bg-white/80 backdrop-blur-md border-b border-gray-100"}`}>
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 font-extrabold text-xl text-brand-600">
              <div className="h-8 w-8 rounded-lg bg-brand-gradient flex items-center justify-center bg-brand-600">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <span>PixelPro</span>
              <span className="hidden sm:inline text-xs font-medium text-brand-400 border border-brand-200 rounded-full px-1.5 py-0.5 ml-1">AI</span>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-1 text-sm font-medium text-gray-600">
              {/* Product dropdown */}
              <div className="relative" onMouseEnter={() => setProductOpen(true)} onMouseLeave={() => setProductOpen(false)}>
                <button className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors">
                  Product <ChevronDown className={`h-3.5 w-3.5 transition-transform ${productOpen ? "rotate-180" : ""}`} />
                </button>
                {productOpen && (
                  <div className="absolute top-full left-0 mt-1 w-72 rounded-xl border border-gray-200 bg-white shadow-xl p-2">
                    {products.map((p) => (
                      <Link key={p.label} href={p.href} className="flex items-center gap-3 rounded-lg px-3 py-2.5 hover:bg-gray-50 transition-colors">
                        <div className="h-9 w-9 rounded-lg bg-brand-50 flex items-center justify-center flex-shrink-0">
                          <p.icon className="h-4 w-4 text-brand-600" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-900 text-sm">{p.label}</p>
                          <p className="text-xs text-gray-500">{p.desc}</p>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
              <Link href="#pricing" className="px-3 py-2 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors">Pricing</Link>
              <Link href="#how-it-works" className="px-3 py-2 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors">How It Works</Link>
              <Link href="/docs" className="px-3 py-2 rounded-lg hover:bg-gray-100 hover:text-gray-900 transition-colors">API</Link>
            </div>

            <div className="hidden md:flex items-center gap-3">
              <Link href="/auth/login" className="text-sm font-medium text-gray-700 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors">
                Log in
              </Link>
              <Link href="/auth/register" className="btn-primary py-2 px-4 text-sm rounded-lg">
                Start Free →
              </Link>
            </div>

            <button className="md:hidden p-2 rounded-lg hover:bg-gray-100" onClick={() => setOpen(!open)}>
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>

          {/* Mobile menu */}
          {open && (
            <div className="md:hidden pb-4 pt-2 flex flex-col gap-1 border-t border-gray-100 mt-2">
              <Link href="/enhance" className="flex items-center gap-2 py-2.5 px-3 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700">
                <Zap className="h-4 w-4 text-brand-500" /> Product Features
              </Link>
              <Link href="#pricing" className="py-2.5 px-3 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700">Pricing</Link>
              <Link href="#how-it-works" className="py-2.5 px-3 rounded-lg hover:bg-gray-50 text-sm font-medium text-gray-700">How It Works</Link>
              <div className="flex gap-2 pt-2">
                <Link href="/auth/login" className="flex-1 btn-secondary py-2.5 text-center text-sm">Log in</Link>
                <Link href="/auth/register" className="flex-1 btn-primary py-2.5 text-center text-sm">Start Free</Link>
              </div>
            </div>
          )}
        </div>
      </nav>
    </>
  );
}
