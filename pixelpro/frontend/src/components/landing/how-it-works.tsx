import Link from "next/link";
import { Upload, Sliders, Download, ArrowRight } from "lucide-react";

const steps = [
  {
    step: "01",
    icon: Upload,
    title: "Upload Your Image",
    description: "Drag and drop any product photo — JPG, PNG, WebP. Up to 20MB. No account needed to try.",
    detail: "Supports single images or batch upload of 100+ files at once.",
    color: "from-blue-500 to-brand-600",
  },
  {
    step: "02",
    icon: Sliders,
    title: "Choose Your Enhancement",
    description: "Pick AI Edit, Nano Banana style, or classic enhance. Type any instruction or pick from presets.",
    detail: "\"Make person wear a suit\", vintage film, 4K upscale — whatever you need.",
    color: "from-purple-500 to-pink-600",
  },
  {
    step: "03",
    icon: Download,
    title: "Download & Sell",
    description: "Your AI-enhanced image is ready in seconds. Download it or push directly to your store.",
    detail: "PNG, JPG, WebP output. Auto-optimized for Amazon, Shopify, Etsy requirements.",
    color: "from-green-500 to-teal-600",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-gray-50">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-600 mb-4">
            Simple Process
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900">
            From Upload to Perfect
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-purple-600">in 3 Steps</span>
          </h2>
          <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto">
            No design skills, no Photoshop, no learning curve. Just results.
          </p>
        </div>

        <div className="relative">
          {/* Connector line */}
          <div className="absolute top-16 left-0 right-0 hidden lg:block">
            <div className="mx-auto max-w-4xl px-32">
              <div className="h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent" />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 relative">
            {steps.map((s, i) => (
              <div key={s.step} className="relative flex flex-col items-center text-center">
                {/* Step number circle */}
                <div className={`relative h-16 w-16 rounded-2xl bg-gradient-to-br ${s.color} flex items-center justify-center shadow-lg mb-6`}>
                  <s.icon className="h-7 w-7 text-white" />
                  <div className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-white border-2 border-gray-100 shadow flex items-center justify-center">
                    <span className="text-xs font-black text-gray-700">{i + 1}</span>
                  </div>
                </div>

                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 w-full">
                  <h3 className="text-xl font-bold text-gray-900 mb-3">{s.title}</h3>
                  <p className="text-gray-600 leading-relaxed mb-3">{s.description}</p>
                  <p className="text-xs text-gray-400 leading-relaxed italic">{s.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12 text-center">
          <Link href="/auth/register"
            className="inline-flex items-center gap-2 rounded-xl border-2 border-brand-600 bg-white px-7 py-3.5 text-sm font-bold text-brand-700 hover:bg-brand-50 transition-all active:scale-95"
          >
            Start for Free <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
