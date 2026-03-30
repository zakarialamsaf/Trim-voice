import { create } from "zustand";
import { persist } from "zustand/middleware";
import Cookies from "js-cookie";
import { authApi } from "./api";

interface User {
  id: string;
  email: string;
  full_name: string | null;
  plan: "free" | "starter" | "pro" | "business";
  credits_remaining: number;
  credits_used_total: number;
  api_key: string | null;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const { data } = await authApi.login(email, password);
        Cookies.set("access_token", data.access_token, {
          expires: 1,
          secure: process.env.NODE_ENV === "production",
          sameSite: "strict",
        });
        Cookies.set("refresh_token", data.refresh_token, {
          expires: 30,
          secure: process.env.NODE_ENV === "production",
          sameSite: "strict",
        });
        // Fetch user profile
        const { default: axios } = await import("axios");
        const { data: user } = await import("./api").then((m) =>
          m.api.get("/users/me", {
            headers: { Authorization: `Bearer ${data.access_token}` },
          })
        );
        set({ user, isAuthenticated: true });
      },

      register: async (email, password, fullName) => {
        await authApi.register(email, password, fullName);
      },

      logout: () => {
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        set({ user: null, isAuthenticated: false });
      },

      setUser: (user) => set({ user, isAuthenticated: true }),
    }),
    {
      name: "pixelpro-auth",
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);
