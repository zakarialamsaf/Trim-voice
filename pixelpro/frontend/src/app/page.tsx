import { HeroSection } from "@/components/landing/hero-section";
import { StatsSection } from "@/components/landing/stats-section";
import { FeaturesSection } from "@/components/landing/features-section";
import { HowItWorks } from "@/components/landing/how-it-works";
import { TestimonialsSection } from "@/components/landing/testimonials-section";
import { PricingSection } from "@/components/landing/pricing-section";
import { FaqSection } from "@/components/landing/faq-section";
import { CTASection } from "@/components/landing/cta-section";
import { Navbar } from "@/components/landing/navbar";
import { Footer } from "@/components/landing/footer";

export const metadata = {
  title: "PixelPro — AI Product Image Enhancer | 4K Upscaling & AI Editing",
  description:
    "Turn blurry product photos into conversion-driving imagery with AI. 4K upscaling, instruction-following edits, Nano Banana styles. Used by 12,000+ ecommerce sellers.",
  keywords: "AI image enhancement, product photography, 4K upscaling, ecommerce images, AI photo editing",
  openGraph: {
    title: "PixelPro — AI Product Image Enhancer",
    description: "Turn blurry product photos into sales machines with AI. Free to start.",
    type: "website",
  },
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <HeroSection />
        <StatsSection />
        <FeaturesSection />
        <HowItWorks />
        <TestimonialsSection />
        <PricingSection />
        <FaqSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
