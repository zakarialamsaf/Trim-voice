"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2, Check } from "lucide-react";
import { authApi } from "@/lib/api";
import { useState } from "react";

const schema = z.object({
  full_name: z.string().min(2).max(100),
  email: z.string().email(),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: "Passwords do not match",
  path: ["confirm_password"],
});

type FormData = z.infer<typeof schema>;

const perks = ["5 free enhancements", "No credit card", "Cancel anytime"];

export default function RegisterPage() {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const router = useRouter();

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      setError(null);
      await authApi.register(data.email, data.password, data.full_name);
      setSuccess(true);
      setTimeout(() => router.push("/auth/login"), 2000);
    } catch (e: any) {
      const msg = e?.response?.data?.detail;
      setError(msg === "Email already registered"
        ? "An account with this email already exists."
        : "Something went wrong. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 font-extrabold text-2xl text-brand-600">
            <Sparkles className="h-7 w-7" />
            PixelPro
          </Link>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">Create your free account</h1>
          <div className="mt-3 flex items-center justify-center gap-4">
            {perks.map((p) => (
              <span key={p} className="flex items-center gap-1 text-xs text-green-700 font-medium">
                <Check className="h-3.5 w-3.5" /> {p}
              </span>
            ))}
          </div>
        </div>

        <div className="card shadow-lg">
          {success ? (
            <div className="text-center py-8">
              <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
                <Check className="h-8 w-8 text-green-600" />
              </div>
              <h2 className="text-lg font-bold text-gray-900">Account created!</h2>
              <p className="text-gray-500 mt-2 text-sm">Redirecting to login…</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
                  {error}
                </div>
              )}
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {[
                  { name: "full_name" as const, label: "Full Name", type: "text", placeholder: "Jane Smith" },
                  { name: "email" as const, label: "Email", type: "email", placeholder: "jane@shop.com" },
                  { name: "password" as const, label: "Password", type: "password", placeholder: "8+ characters" },
                  { name: "confirm_password" as const, label: "Confirm Password", type: "password", placeholder: "Repeat password" },
                ].map(({ name, label, type, placeholder }) => (
                  <div key={name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
                    <input
                      {...register(name)}
                      type={type}
                      className="input"
                      placeholder={placeholder}
                    />
                    {errors[name] && (
                      <p className="mt-1 text-xs text-red-600">{errors[name]?.message}</p>
                    )}
                  </div>
                ))}
                <button type="submit" disabled={isSubmitting} className="btn-primary w-full">
                  {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Create Free Account
                </button>
              </form>
              <p className="mt-4 text-center text-xs text-gray-500">
                By signing up you agree to our{" "}
                <Link href="/terms" className="text-brand-600 hover:underline">Terms</Link> and{" "}
                <Link href="/privacy" className="text-brand-600 hover:underline">Privacy Policy</Link>.
              </p>
            </>
          )}
        </div>

        <p className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link href="/auth/login" className="font-semibold text-brand-600 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
