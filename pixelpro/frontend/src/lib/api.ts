import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import Cookies from "js-cookie";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 60000,
});

// ── Request interceptor: attach auth token ─────────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: auto-refresh on 401 ──────────────────────────────
let isRefreshing = false;
let failedQueue: Array<{ resolve: (t: string) => void; reject: (e: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }

      original._retry = true;
      isRefreshing = true;

      const refreshToken = Cookies.get("refresh_token");
      if (!refreshToken) {
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        window.location.href = "/auth/login";
        return Promise.reject(error);
      }

      try {
        const { data } = await api.post("/auth/refresh", { refresh_token: refreshToken });
        Cookies.set("access_token", data.access_token, { expires: 1, secure: true, sameSite: "strict" });
        processQueue(null, data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (refreshError) {
        processQueue(refreshError, null);
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");
        window.location.href = "/auth/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ── Typed API helpers ──────────────────────────────────────────────────────

export interface EnhancementOptions {
  upscale_factor?: number;
  denoise?: boolean;
  sharpen?: boolean;
  color_correct?: boolean;
  face_enhance?: boolean;
  remove_background?: boolean;
  output_format?: "png" | "jpg" | "webp";
  output_quality?: number;
}

export const imageApi = {
  upload: (file: File, options: EnhancementOptions) => {
    const form = new FormData();
    form.append("file", file);
    Object.entries(options).forEach(([k, v]) => form.append(k, String(v)));
    return api.post("/images/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  getStatus: (imageId: string) => api.get(`/images/${imageId}/status`),
  getImage: (imageId: string) => api.get(`/images/${imageId}`),
  listImages: (page = 1, perPage = 20) =>
    api.get("/images/", { params: { page, per_page: perPage } }),

  uploadBatch: (files: File[], options: EnhancementOptions) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("enhancement_options", JSON.stringify(options));
    return api.post("/images/batch", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ── Transform (Nano Banana + styles) ──────────────────────────────────────────

export type NanaBananaStyle =
  | "nano_banana"
  | "nano_banana_2"
  | "nano_banana_pro"
  | "product_pro"
  | "vintage"
  | "cyberpunk";

export interface TransformResult {
  image_id: string;
  status: string;
  style: string;
  prompt: string;
  original_url: string;
  transformed_url: string;
  original_width: number;
  original_height: number;
  output_width: number;
  output_height: number;
  credits_used: number;
  message: string;
}

export interface ImageAnalysis {
  image_info: {
    width: number;
    height: number;
    megapixels: number;
    brightness: number;
    contrast: number;
    sharpness_score: number;
    has_faces: boolean;
    face_count: number;
    is_low_resolution: boolean;
    is_dark: boolean;
    is_noisy: boolean;
    is_desaturated: boolean;
  };
  suggestions: Array<{
    id: string;
    icon: string;
    title: string;
    description: string;
    tags: string[];
    preview_effect: string;
    confidence: number;
  }>;
}

export interface EditResult {
  image_id: string;
  status: string;
  prompt: string;
  original_url: string;
  edited_url: string;
  original_width: number;
  original_height: number;
  output_width: number;
  output_height: number;
  credits_used: number;
  message: string;
}

export interface ProviderStatus {
  fal_ai: { available: boolean; model: string; quality: string; setup_url: string; env_var: string; free_tier: boolean; description: string };
  huggingface: { available: boolean; model: string; quality: string; setup_url: string; env_var: string; free_tier: boolean; description: string };
  gradio_spaces?: { available: boolean; model: string; quality: string; setup_url: string; env_var: string | null; free_tier: boolean; description: string };
}

export const transformApi = {
  analyze: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<ImageAnalysis>("/transform/analyze", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  nanaBanana: (file: File, style: NanaBananaStyle, prompt = "") => {
    const form = new FormData();
    form.append("file", file);
    form.append("style", style);
    form.append("prompt", prompt);
    return api.post<TransformResult>("/transform/nano-banana", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120_000,
    });
  },

  edit: (file: File, prompt: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("prompt", prompt);
    return api.post<EditResult>("/transform/edit", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 180_000,
    });
  },

  providerStatus: () => api.get<ProviderStatus>("/transform/provider-status"),
};

export const userApi = {
  getMe: () => api.get("/users/me"),
  updateMe: (data: { full_name?: string; password?: string }) => api.patch("/users/me", data),
  getDashboard: () => api.get("/users/me/dashboard"),
  regenerateApiKey: () => api.post("/users/me/regenerate-api-key"),
};

export const authApi = {
  login: (email: string, password: string) => {
    const form = new URLSearchParams({ username: email, password });
    return api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  register: (email: string, password: string, full_name?: string) =>
    api.post("/auth/register", { email, password, full_name }),
  refresh: (refreshToken: string) => api.post("/auth/refresh", { refresh_token: refreshToken }),
};
