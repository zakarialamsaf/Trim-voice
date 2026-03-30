import { Star, Quote } from "lucide-react";

const testimonials = [
  {
    quote: "We went from 3.2% to 5.8% conversion rate after running our product catalog through PixelPro. The ROI was instant — paid for a year in the first week.",
    author: "Sarah K.",
    role: "Head of Ecommerce",
    company: "NordStyle",
    avatar: "SK",
    color: "bg-blue-600",
    rating: 5,
    metric: "+81% conversion",
  },
  {
    quote: "I used to spend 2 hours per product in Lightroom. Now I batch-enhance 200 images in 10 minutes. The AI Edit feature is witchcraft — I typed 'remove the background and add studio lighting' and it just worked.",
    author: "Marcus T.",
    role: "Product Photographer",
    company: "Freelance",
    avatar: "MT",
    color: "bg-purple-600",
    rating: 5,
    metric: "12× faster workflow",
  },
  {
    quote: "Our Amazon listings look as professional as competitors with £50k studio setups — and we're a 2-person team. PixelPro is genuinely a competitive advantage.",
    author: "Priya M.",
    role: "Founder",
    company: "GlowCraft Beauty",
    avatar: "PM",
    color: "bg-rose-600",
    rating: 5,
    metric: "+43% Amazon CTR",
  },
  {
    quote: "The Nano Banana styles went viral on our TikTok shop. We turned boring product shots into collectible toy aesthetics and our engagement tripled overnight.",
    author: "Jake L.",
    role: "Social Commerce Manager",
    company: "TrendDrop",
    avatar: "JL",
    color: "bg-amber-600",
    rating: 5,
    metric: "3× TikTok engagement",
  },
  {
    quote: "We process 5,000 images a month through the API. The batch processing is rock solid and the image quality beats every tool we've tried including Topaz.",
    author: "Chen W.",
    role: "CTO",
    company: "StyleStack",
    avatar: "CW",
    color: "bg-teal-600",
    rating: 5,
    metric: "5,000 imgs/month",
  },
  {
    quote: "Set up took 5 minutes. The API docs are clear, the credits system is fair, and support actually responds. Rare for a SaaS product at this price point.",
    author: "Anna R.",
    role: "Developer",
    company: "Boutique Agency",
    avatar: "AR",
    color: "bg-indigo-600",
    rating: 5,
    metric: "5-min integration",
  },
];

export function TestimonialsSection() {
  return (
    <section className="py-24 bg-white overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-semibold text-gray-600 mb-4">
            Customer Stories
          </div>
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900">
            Sellers Love the Results
          </h2>
          <p className="mt-4 text-lg text-gray-500">Real outcomes from real customers — not cherry-picked agency shots.</p>
          <div className="mt-4 flex items-center justify-center gap-2">
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="h-5 w-5 fill-yellow-400 text-yellow-400" />
              ))}
            </div>
            <span className="font-bold text-gray-900">4.9/5</span>
            <span className="text-gray-500 text-sm">across 2,400+ reviews</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((t) => (
            <div key={t.author}
              className="group relative flex flex-col gap-4 rounded-2xl border border-gray-100 bg-white p-6 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
            >
              {/* Metric badge */}
              <div className="absolute top-5 right-5 rounded-full bg-green-50 border border-green-100 px-2.5 py-1 text-xs font-bold text-green-700">
                {t.metric}
              </div>

              {/* Stars */}
              <div className="flex gap-0.5">
                {[...Array(t.rating)].map((_, i) => (
                  <Star key={i} className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>

              {/* Quote */}
              <p className="text-gray-700 leading-relaxed text-sm flex-1">"{t.quote}"</p>

              {/* Author */}
              <div className="flex items-center gap-3 pt-4 border-t border-gray-50">
                <div className={`h-10 w-10 rounded-full ${t.color} flex items-center justify-center text-white text-xs font-bold flex-shrink-0`}>
                  {t.avatar}
                </div>
                <div>
                  <p className="font-bold text-gray-900 text-sm">{t.author}</p>
                  <p className="text-gray-400 text-xs">{t.role} · {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Trust logos */}
        <div className="mt-16 rounded-2xl bg-gray-50 border border-gray-100 p-8 text-center">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-6">Featured & Reviewed By</p>
          <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4">
            {["Product Hunt", "Indie Hackers", "AppSumo", "G2", "Capterra", "TechCrunch"].map((name) => (
              <span key={name} className="text-lg font-black text-gray-300 hover:text-gray-500 transition-colors cursor-default">{name}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
