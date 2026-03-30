"use client";
import { useState } from "react";
import { ChevronDown } from "lucide-react";

const faqs = [
  {
    q: "How does the free trial work?",
    a: "You get 3 days of full Pro access — completely free, no credit card required. You can use every feature including AI Edit, Nano Banana styles, batch processing and more. After 3 days, you can subscribe to Pro for just $10/month or stop — no charges ever without your consent.",
  },
  {
    q: "What image formats are supported?",
    a: "We accept JPG, PNG, and WebP files up to 20MB. You can output in any of these formats. For batch processing, zip archives are also supported.",
  },
  {
    q: "How does AI Edit work? (e.g., 'make person wear a suit')",
    a: "AI Edit uses state-of-the-art instruction-following models (FLUX.1 Kontext via fal.ai, or Qwen Image Edit). You type a natural language instruction and the AI modifies the image content — changing outfits, backgrounds, lighting, hair colour, and more.",
  },
  {
    q: "What is Nano Banana?",
    a: "Nano Banana is a viral aesthetic trend that transforms regular images into collectible toy / figurine style photography. We offer 6 presets: Classic Nano Banana, Pastel, PRO Metallic, Product Pro, Vintage Film, and Cyberpunk — all rendered locally with no extra API costs.",
  },
  {
    q: "Is there an API for bulk processing?",
    a: "Yes! All paid plans include API access. You can upload images, poll for status, and download results programmatically. Batch endpoints support up to 10 images (Starter), 50 (Pro), or unlimited (Business). Check /docs for the OpenAPI spec.",
  },
  {
    q: "Are my images stored? Is it secure?",
    a: "Images are processed and stored temporarily (30 days) then permanently deleted. All files are encrypted in transit (SSL) and at rest. We are GDPR-compliant. We never use your images to train models.",
  },
  {
    q: "Can I cancel my plan at any time?",
    a: "Yes, you can cancel any time from your dashboard. You keep your credits until the end of the billing period. No cancellation fees, no lock-in.",
  },
  {
    q: "Do you offer refunds?",
    a: "If you're not happy with results in the first 7 days, we offer a full refund. Just email support. After that, we can refund unused credits at our discretion.",
  },
];

export function FaqSection() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <section className="py-24 bg-gray-50">
      <div className="mx-auto max-w-3xl px-6 lg:px-8">
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-600 mb-4">
            FAQ
          </div>
          <h2 className="text-4xl font-extrabold text-gray-900">Questions & Answers</h2>
          <p className="mt-3 text-gray-500">Everything you need to know about PixelPro.</p>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <div key={i}
              className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-gray-50 transition-colors"
              >
                <span className="font-semibold text-gray-900 text-sm pr-4">{faq.q}</span>
                <ChevronDown className={`h-4 w-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${open === i ? "rotate-180" : ""}`} />
              </button>
              {open === i && (
                <div className="px-6 pb-5">
                  <p className="text-sm text-gray-600 leading-relaxed">{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-gray-500">
          Still have questions?{" "}
          <a href="mailto:hello@pixelpro.ai" className="text-brand-600 font-semibold hover:underline">
            Email us →
          </a>
        </p>
      </div>
    </section>
  );
}
