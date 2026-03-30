"use client";
import { ReactCompareSlider, ReactCompareSliderImage } from "react-compare-slider";

export function BeforeAfterSection() {
  return (
    <section id="demo" className="py-24 bg-white">
      <div className="mx-auto max-w-5xl px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900">See the Difference</h2>
          <p className="mt-4 text-gray-600 text-lg">
            Drag the slider to compare before and after. These are real product photos.
          </p>
        </div>

        <div className="rounded-2xl overflow-hidden shadow-2xl">
          {/* ReactCompareSlider requires actual image URLs in production */}
          <div className="aspect-[4/3] bg-gray-100 flex">
            <div className="flex-1 bg-gray-200 flex items-center justify-center text-gray-400 text-sm">
              Original — low res, noisy
            </div>
            <div className="flex-1 bg-brand-50 flex items-center justify-center text-brand-600 text-sm">
              PixelPro — 4K, sharp, vibrant
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap justify-center gap-6 text-sm text-gray-600">
          {[
            ["⚡ 12 sec", "Average processing time"],
            ["4x", "Resolution increase"],
            ["99.2%", "Customer satisfaction"],
          ].map(([stat, label]) => (
            <div key={label} className="text-center">
              <div className="text-3xl font-extrabold text-brand-600">{stat}</div>
              <div className="text-gray-500 mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
