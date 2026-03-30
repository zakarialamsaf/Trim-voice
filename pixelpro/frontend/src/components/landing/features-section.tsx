import Link from "next/link";
import { Maximize2, Eraser, Scan, Palette, User, ImageOff, Wand2, Banana, ArrowRight } from "lucide-react";

const features = [
  {
    icon: Maximize2,
    title: "4× Super Resolution",
    description: "Real-ESRGAN AI upscales to 4K without blurry artifacts. Perfect for marketplace hero shots.",
    badge: "Most Used",
    color: "bg-blue-50 text-blue-600",
  },
  {
    icon: Wand2,
    title: "AI Instruction Editing",
    description: "Type any instruction — \"make person wear a suit\", \"change background to beach\" — and AI does it.",
    badge: "New ✨",
    color: "bg-purple-50 text-purple-600",
  },
  {
    icon: Banana,
    title: "Nano Banana Styles",
    description: "6 viral aesthetic presets — toy figurine, cyberpunk, vintage, product-pro and more. Trend-ready.",
    badge: "Trending 🔥",
    color: "bg-yellow-50 text-yellow-600",
  },
  {
    icon: Eraser,
    title: "Smart Denoising",
    description: "Remove grain, JPEG artifacts, and sensor noise while preserving fine product textures and details.",
    color: "bg-green-50 text-green-600",
  },
  {
    icon: Palette,
    title: "Auto Color Correction",
    description: "Fix white balance, boost contrast, and make colors pop. Products look as good online as in person.",
    color: "bg-orange-50 text-orange-600",
  },
  {
    icon: User,
    title: "Face Restoration",
    description: "GFPGAN-powered face enhancement for fashion and lifestyle product shots featuring models.",
    color: "bg-rose-50 text-rose-600",
  },
  {
    icon: Scan,
    title: "AI Sharpening",
    description: "Unsharp masking brings out edges and fine details — essential for fabric, jewelry, and electronics.",
    color: "bg-teal-50 text-teal-600",
  },
  {
    icon: ImageOff,
    title: "Background Removal",
    description: "One-click clean white background for Amazon, Etsy, Shopify listings. Studio quality, zero effort.",
    badge: "Pro+",
    color: "bg-indigo-50 text-indigo-600",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-white">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 mb-4">
            Complete AI Pipeline
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900">
            Everything Your Photos Need
          </h2>
          <p className="mt-4 text-lg text-gray-500 max-w-2xl mx-auto">
            Not just upscaling. A full suite of AI tools tuned specifically for ecommerce — from raw shot to sales-ready image.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((feature, i) => (
            <div key={feature.title}
              className="relative group rounded-2xl border border-gray-100 bg-white p-6 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
            >
              {feature.badge && (
                <span className="absolute top-4 right-4 rounded-full bg-brand-50 border border-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700">
                  {feature.badge}
                </span>
              )}
              <div className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${feature.color} mb-4`}>
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-500 text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link href="/auth/register"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-7 py-3.5 text-sm font-bold text-white shadow-md hover:bg-brand-700 hover:-translate-y-0.5 transition-all active:scale-95"
          >
            Try All Features Free <ArrowRight className="h-4 w-4" />
          </Link>
          <p className="mt-3 text-xs text-gray-400">3 days free · No card required · $10/mo after</p>
        </div>
      </div>
    </section>
  );
}
