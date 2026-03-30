"use client";
import { useEffect, useRef, useState } from "react";

const STATS = [
  { value: 3200000, label: "Images Enhanced", suffix: "+", prefix: "" },
  { value: 12000, label: "Active Sellers", suffix: "+", prefix: "" },
  { value: 4.9, label: "Average Rating", suffix: "/5", prefix: "" },
  { value: 2.4, label: "Avg. Process Time", suffix: "s", prefix: "" },
];

function useCountUp(target: number, duration = 1800, started: boolean) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!started) return;
    const isFloat = target % 1 !== 0;
    const steps = 60;
    const stepTime = duration / steps;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(isFloat ? parseFloat((target * eased).toFixed(1)) : Math.round(target * eased));
      if (step >= steps) clearInterval(timer);
    }, stepTime);
    return () => clearInterval(timer);
  }, [target, duration, started]);
  return count;
}

function StatCard({ value, label, suffix, prefix, started }: typeof STATS[0] & { started: boolean }) {
  const count = useCountUp(value, 1800, started);
  const formatted = value >= 1000000
    ? (count / 1000000).toFixed(1) + "M"
    : value >= 1000
    ? (count / 1000).toFixed(0) + "K"
    : count;
  return (
    <div className="text-center group">
      <div className="text-4xl md:text-5xl font-extrabold text-gray-900 tabular-nums group-hover:text-brand-600 transition-colors">
        {prefix}{formatted}{suffix}
      </div>
      <div className="mt-2 text-sm font-medium text-gray-500 uppercase tracking-wide">{label}</div>
    </div>
  );
}

export function StatsSection() {
  const ref = useRef<HTMLDivElement>(null);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setStarted(true); },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="py-16 bg-gradient-to-b from-white to-gray-50 border-y border-gray-100">
      <div className="mx-auto max-w-5xl px-6 lg:px-8" ref={ref}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          {STATS.map((s) => (
            <StatCard key={s.label} {...s} started={started} />
          ))}
        </div>
      </div>
    </section>
  );
}
