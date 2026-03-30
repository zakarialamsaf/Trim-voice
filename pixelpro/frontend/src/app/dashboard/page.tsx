"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useAuthStore } from "@/lib/auth-store";
import { userApi } from "@/lib/api";
import { ImagePlus, Zap, CheckCircle2, XCircle, Clock, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => userApi.getDashboard().then((r) => r.data),
  });

  const creditPct = user
    ? Math.round((user.credits_remaining / (user.credits_remaining + user.credits_used_total)) * 100)
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}!
          </h1>
          <p className="text-gray-600 mt-1">
            You&apos;re on the{" "}
            <span className="font-semibold text-brand-600 capitalize">{user?.plan}</span> plan.
          </p>
        </div>
        <Link href="/enhance" className="btn-primary">
          <ImagePlus className="h-4 w-4" />
          Enhance Images
        </Link>
      </div>

      {/* Credit bar */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-brand-600" />
            <span className="font-semibold text-gray-900">Credits</span>
          </div>
          <span className="text-sm text-gray-500">
            <span className="font-bold text-gray-900">{user?.credits_remaining}</span> remaining
          </span>
        </div>
        <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand-600 transition-all"
            style={{ width: `${Math.min(creditPct, 100)}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5 text-xs text-gray-500">
          <span>{user?.credits_used_total} used this month</span>
          {user?.plan === "free" && (
            <Link href="/pricing" className="text-brand-600 font-medium hover:underline">
              Upgrade for more →
            </Link>
          )}
        </div>
      </div>

      {/* Stats */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse h-24 bg-gray-100" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Images", value: data?.stats.total_images, icon: ImagePlus, color: "text-blue-600" },
            { label: "This Month", value: data?.stats.monthly_images, icon: TrendingUp, color: "text-purple-600" },
            { label: "Completed", value: data?.stats.completed, icon: CheckCircle2, color: "text-green-600" },
            { label: "Failed", value: data?.stats.failed, icon: XCircle, color: "text-red-500" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="card">
              <div className={`${color} mb-2`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="text-2xl font-bold text-gray-900">{value ?? "—"}</div>
              <div className="text-xs text-gray-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Recent images */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Recent Enhancements</h2>
          <Link href="/enhance/history" className="text-sm text-brand-600 hover:underline">
            View all
          </Link>
        </div>

        {data?.recent_images?.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <ImagePlus className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">No images yet</p>
            <Link href="/enhance" className="mt-4 btn-primary inline-flex">
              Enhance your first image
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {data?.recent_images?.map((img: any) => (
              <div key={img.id} className="py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`h-2 w-2 rounded-full ${
                    img.status === "completed" ? "bg-green-500" :
                    img.status === "failed" ? "bg-red-500" :
                    "bg-yellow-500 animate-pulse"
                  }`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{img.filename}</p>
                    <p className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(img.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <Link
                  href={`/enhance/${img.id}`}
                  className="text-xs text-brand-600 font-medium hover:underline"
                >
                  View
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
