"use client";
import Link from "next/link";
import { ArrowRight, Sparkles, Zap, Star, Play, Check } from "lucide-react";
import { motion } from "framer-motion";


const TRUST_ITEMS = [
  "No credit card required",
  "3 days fully free",
  "Results in seconds",
];

const PLATFORMS = ["Amazon", "Shopify", "Etsy", "eBay", "WooCommerce", "Squarespace"];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-white pt-8 pb-20">
      {/* Animated background blobs */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-[700px] h-[700px] rounded-full bg-brand-500/8 blur-3xl animate-pulse" />
        <div className="absolute top-20 -left-40 w-[500px] h-[500px] rounded-full bg-purple-500/6 blur-3xl" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[900px] h-[300px] rounded-full bg-brand-400/5 blur-3xl" />
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:60px_60px] opacity-40" />
      </div>

      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Badge */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          className="flex justify-center mb-8"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-1.5 text-sm font-semibold text-brand-700 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-500 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-600" />
            </span>
            Now with AI Instruction Editing — FLUX.1 Kontext
          </div>
        </motion.div>

        {/* Headline */}
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}
          className="text-center"
        >
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-gray-900 leading-[1.08]">
            Your Product Photos,
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 via-purple-600 to-brand-500">
              10× More Powerful
            </span>
          </h1>
          <p className="mt-6 mx-auto max-w-2xl text-xl text-gray-500 leading-relaxed">
            AI upscaling, style transforms, and instruction-following edits — all in one platform.
            Turn blurry product shots into conversion-driving imagery in <strong className="text-gray-700">seconds</strong>.
          </p>
        </motion.div>

        {/* CTA Buttons */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.25 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Link href="/auth/register"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-brand-500/25 hover:bg-brand-700 hover:shadow-brand-500/40 hover:-translate-y-0.5 transition-all active:scale-95"
          >
            <Sparkles className="h-5 w-5" />
            Start 3-Day Free Trial
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link href="#demo"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-8 py-4 text-base font-semibold text-gray-700 shadow-sm hover:bg-gray-50 hover:border-gray-300 transition-all active:scale-95"
          >
            <div className="h-6 w-6 rounded-full bg-brand-100 flex items-center justify-center">
              <Play className="h-3 w-3 text-brand-600 fill-brand-600 ml-0.5" />
            </div>
            Watch Demo
          </Link>
        </motion.div>

        {/* Trust line */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2"
        >
          {TRUST_ITEMS.map((item) => (
            <div key={item} className="flex items-center gap-1.5 text-sm text-gray-500">
              <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
              {item}
            </div>
          ))}
        </motion.div>

        {/* Social proof bar */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500"
        >
          <div className="flex items-center gap-1.5">
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              ))}
            </div>
            <span className="font-semibold text-gray-700">4.9/5</span>
            <span>from 2,400+ reviews</span>
          </div>
          <div className="h-4 w-px bg-gray-200 hidden sm:block" />
          <div className="flex items-center gap-1.5">
            <Zap className="h-4 w-4 text-brand-500" />
            <span className="font-semibold text-gray-700">3.2M+</span> images enhanced
          </div>
          <div className="h-4 w-px bg-gray-200 hidden sm:block" />
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-green-500 inline-block" />
            <span className="font-semibold text-gray-700">12,000+</span> active sellers
          </div>
        </motion.div>

        {/* Hero Visual — Before/After */}
        <motion.div initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, delay: 0.3 }}
          className="mt-14 mx-auto max-w-5xl"
        >
          <div className="relative rounded-2xl overflow-hidden shadow-2xl border border-gray-800 bg-gray-950">
            <div className="flex h-80 md:h-[420px]">

              {/* ── BEFORE panel ── */}
              <div className="relative w-1/2 overflow-hidden flex items-center justify-center bg-gray-900">
                {/* Real product image — blurry/noisy version */}
                <img
                  src="/demo-before.jpg"
                  alt="Before AI enhancement"
                  className="w-full h-full object-cover"
                  style={{ filter: "blur(0.5px) contrast(0.8) saturate(0.5) brightness(0.85)" }}
                />
                {/* Scanline overlay */}
                <div className="absolute inset-0 pointer-events-none opacity-20"
                  style={{ backgroundImage: "repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.3) 4px)" }}
                />
                {/* Labels */}
                <div className="absolute top-4 left-4 flex flex-col gap-1.5">
                  <span className="bg-red-500 rounded-md px-2.5 py-1 text-white text-[11px] font-bold uppercase tracking-wide shadow">Before</span>
                  <span className="text-white/50 text-[10px] font-mono drop-shadow">72dpi · noisy · blurry</span>
                </div>
                <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-sm border border-white/10 rounded-md px-2.5 py-1 text-white/60 text-[10px] font-mono">
                  480 × 480px
                </div>
              </div>

              {/* ── Divider ── */}
              <div className="relative z-10 w-0 flex items-center justify-center flex-shrink-0">
                <div className="absolute w-0.5 h-full bg-gradient-to-b from-transparent via-white/50 to-transparent" />
                <div className="relative h-10 w-10 rounded-full bg-white shadow-2xl flex items-center justify-center border-2 border-gray-100 z-10 -translate-x-1/2">
                  <Sparkles className="h-4 w-4 text-brand-600" />
                </div>
              </div>

              {/* ── AFTER panel ── */}
              <div className="relative w-1/2 overflow-hidden flex items-center justify-center bg-gray-950">
                {/* Subtle glow behind image */}
                <div className="absolute inset-0 pointer-events-none"
                  style={{ background: "radial-gradient(ellipse at 55% 45%, rgba(139,92,246,0.15) 0%, transparent 65%)" }}
                />
                {/* Real product image — enhanced version */}
                <img
                  src="/demo-after.jpg"
                  alt="After AI enhancement"
                  className="w-full h-full object-cover"
                  style={{ filter: "contrast(1.08) saturate(1.25) brightness(1.05)" }}
                />
                {/* Sparkle dots */}
                <div className="absolute top-5 right-10 w-2 h-2 rounded-full bg-yellow-300 animate-ping opacity-75" />
                <div className="absolute top-12 right-6 w-1.5 h-1.5 rounded-full bg-white animate-pulse" style={{ animationDelay: "0.4s" }} />
                <div className="absolute top-20 right-14 w-1 h-1 rounded-full bg-purple-300 animate-pulse" style={{ animationDelay: "0.8s" }} />
                {/* Labels */}
                <div className="absolute top-4 right-4 flex flex-col items-end gap-1.5">
                  <span className="bg-green-500 rounded-md px-2.5 py-1 text-white text-[11px] font-bold uppercase tracking-wide shadow">After ✨</span>
                  <span className="text-green-400/80 text-[10px] font-mono drop-shadow">4K · sharp · vivid</span>
                </div>
                <div className="absolute bottom-4 right-4 bg-black/70 backdrop-blur-sm border border-green-500/20 rounded-md px-2.5 py-1 text-green-400/80 text-[10px] font-mono">
                  1920 × 1920px ✓
                </div>
              </div>
            </div>

            {/* ── Bottom bar ── */}
            <div className="bg-gray-950 border-t border-gray-800 px-6 py-3 flex items-center justify-between">
              <div className="flex items-center gap-5 text-xs text-gray-500">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-gray-300">Processing complete</span>
                </span>
                <span>⚡ 2.4 seconds</span>
                <span className="hidden sm:inline">4× upscale · denoised · sharpened</span>
              </div>
              <Link href="/auth/register" className="text-xs font-bold text-brand-400 hover:text-brand-300 transition-colors flex items-center gap-1">
                Try your image free <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </div>
        </motion.div>

        {/* Platform logos */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.7 }}
          className="mt-14 text-center"
        >
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-6">
            Trusted by sellers on
          </p>
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
            {PLATFORMS.map((p) => (
              <span key={p} className="text-base font-bold text-gray-300 hover:text-gray-500 transition-colors cursor-default">
                {p}
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
