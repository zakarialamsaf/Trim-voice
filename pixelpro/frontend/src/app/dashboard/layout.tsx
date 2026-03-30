"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import {
  LayoutDashboard,
  ImagePlus,
  History,
  CreditCard,
  Settings,
  LogOut,
  Sparkles,
  Key,
} from "lucide-react";
import { useEffect } from "react";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/enhance", icon: ImagePlus, label: "Enhance" },
  { href: "/enhance/history", icon: History, label: "History" },
  { href: "/pricing", icon: CreditCard, label: "Upgrade" },
  { href: "/dashboard/api", icon: Key, label: "API" },
  { href: "/dashboard/settings", icon: Settings, label: "Settings" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) router.push("/auth/login");
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col fixed inset-y-0 left-0 z-30">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <Link href="/" className="flex items-center gap-2 font-extrabold text-lg text-brand-600">
            <Sparkles className="h-5 w-5" />
            PixelPro
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ href, icon: Icon, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <Icon className="h-4.5 w-4.5" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-9 w-9 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-bold">
              {user?.full_name?.[0] ?? user?.email[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">
                {user?.full_name ?? user?.email}
              </p>
              <p className="text-xs text-gray-500 capitalize">{user?.plan} plan</p>
            </div>
          </div>
          <button
            onClick={() => { logout(); router.push("/"); }}
            className="flex items-center gap-2 w-full rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-64">{children}</main>
    </div>
  );
}
