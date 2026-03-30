"use client";
import { Check, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const plans = [
  {
    name: "Free Trial",
    price: { monthly: 0, annual: 0 },
    description: "3 days free — no card needed",
    credits: "Full access for 3 days",
    badge: "Start Free",
    features: [
      "3 days full Pro access",
      "AI Instruction Editing",
      "Nano Banana styles",
      "4x upscaling & denoising",
      "Background removal",
      "Color correction",
      "PNG / JPG / WebP output",
    ],
    cta: "Start Free Trial — No Card",
    href: "/auth/register",
    highlighted: false,
  },
  {
    name: "Pro",
    price: { monthly: 10, annual: 8 },
    description: "Everything, every month",
    credits: "500 images/month",
    badge: "Most Popular",
    features: [
      "Everything in Free Trial",
      "500 image credits/month",
      "AI Edit (instruction-following)",
      "Nano Banana + all styles",
      "Batch upload (50 images)",
      "API access + webhooks",
      "Priority queue & support",
    ],
    cta: "Get Pro — $10/month",
    href: "/auth/register?plan=pro",
    highlighted: true,
  },
];

export function PricingSection() {
  const [annual, setAnnual] = useState(false);

  return (
    <section id="pricing" className="py-24 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900">Simple, Predictable Pricing</h2>
          <p className="mt-4 text-lg text-gray-600">No hidden fees. Cancel any time.</p>

          {/* Toggle */}
          <div className="mt-6 inline-flex items-center gap-3 rounded-full bg-gray-100 p-1">
            <button
              onClick={() => setAnnual(false)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                !annual ? "bg-white shadow text-gray-900" : "text-gray-500"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setAnnual(true)}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                annual ? "bg-white shadow text-gray-900" : "text-gray-500"
              }`}
            >
              Annual
              <span className="ml-1.5 text-xs text-green-600 font-semibold">-20%</span>
            </button>
          </div>
        </div>

        <div className="mx-auto max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl p-8 flex flex-col ${
                plan.highlighted
                  ? "bg-brand-600 text-white shadow-2xl ring-2 ring-brand-500 ring-offset-2"
                  : "bg-white border border-gray-200 shadow-sm"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className={`rounded-full px-4 py-1 text-xs font-bold shadow-lg ${
                    plan.highlighted ? "bg-yellow-400 text-yellow-900" : "bg-brand-600 text-white"
                  }`}>
                    {plan.badge}
                  </span>
                </div>
              )}

              <div className="mb-6">
                <h3 className={`text-2xl font-extrabold ${plan.highlighted ? "text-white" : "text-gray-900"}`}>
                  {plan.name}
                </h3>
                <p className={`text-sm mt-1 ${plan.highlighted ? "text-brand-200" : "text-gray-500"}`}>
                  {plan.description}
                </p>
                <div className="mt-5 flex items-baseline gap-1">
                  {plan.price.monthly === 0 ? (
                    <span className={`text-5xl font-extrabold ${plan.highlighted ? "text-white" : "text-gray-900"}`}>
                      Free
                    </span>
                  ) : (
                    <>
                      <span className={`text-5xl font-extrabold ${plan.highlighted ? "text-white" : "text-gray-900"}`}>
                        ${annual ? plan.price.annual : plan.price.monthly}
                      </span>
                      <span className={`text-base ${plan.highlighted ? "text-brand-200" : "text-gray-500"}`}>
                        /month
                      </span>
                      {annual && (
                        <span className="ml-2 text-xs font-bold text-green-400 bg-green-900/30 px-2 py-0.5 rounded-full">
                          Save 20%
                        </span>
                      )}
                    </>
                  )}
                </div>
                <p className={`text-sm mt-2 font-semibold ${plan.highlighted ? "text-yellow-300" : "text-brand-600"}`}>
                  {plan.credits}
                </p>
              </div>

              <ul className="space-y-3 flex-1 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-3 text-sm">
                    <Check className={`h-4 w-4 mt-0.5 flex-shrink-0 ${plan.highlighted ? "text-yellow-300" : "text-brand-600"}`} />
                    <span className={plan.highlighted ? "text-brand-100" : "text-gray-700"}>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`py-3.5 px-6 rounded-xl font-bold text-sm text-center transition-all active:scale-95 ${
                  plan.highlighted
                    ? "bg-white text-brand-700 hover:bg-brand-50 shadow-lg"
                    : "bg-brand-600 text-white hover:bg-brand-700 shadow-md"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-gray-500">
          No credit card for the free trial · Cancel Pro any time · GDPR-compliant · 99.9% uptime
        </p>
      </div>
    </section>
  );
}
