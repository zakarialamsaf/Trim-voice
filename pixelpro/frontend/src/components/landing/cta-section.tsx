import Link from "next/link";
import { ArrowRight, Sparkles, Zap, Shield } from "lucide-react";

export function CTASection() {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-600 via-purple-700 to-brand-800" />
      <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:40px_40px]" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full bg-white/5 blur-3xl" />

      <div className="relative mx-auto max-w-4xl px-6 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm font-semibold text-white mb-8 backdrop-blur-sm">
          <Sparkles className="h-3.5 w-3.5" />
          Start for free · No card needed
        </div>

        <h2 className="text-4xl md:text-6xl font-extrabold text-white leading-tight">
          Ready to Make Your Products
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 to-orange-300">
            Look Irresistible?
          </span>
        </h2>

        <p className="mt-6 text-xl text-brand-100 max-w-xl mx-auto leading-relaxed">
          Join 12,000+ sellers who boosted conversions with AI-enhanced product photography.
          <strong className="text-white"> 3 days fully free</strong> — no card needed.
          Then just <strong className="text-yellow-300">$10/month</strong> for Pro.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/auth/register"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-8 py-4 text-base font-bold text-brand-700 shadow-2xl hover:bg-brand-50 hover:-translate-y-0.5 transition-all active:scale-95"
          >
            <Sparkles className="h-5 w-5" />
            Start 3-Day Free Trial
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link href="#pricing"
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/30 bg-white/10 backdrop-blur-sm px-8 py-4 text-base font-semibold text-white hover:bg-white/20 transition-all active:scale-95"
          >
            View Pricing
          </Link>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-brand-200">
          <div className="flex items-center gap-1.5">
            <Zap className="h-4 w-4" /> Results in seconds
          </div>
          <div className="flex items-center gap-1.5">
            <Shield className="h-4 w-4" /> GDPR compliant
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-4 w-4" /> Cancel any time
          </div>
        </div>
      </div>
    </section>
  );
}
