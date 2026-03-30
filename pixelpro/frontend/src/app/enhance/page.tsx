"use client";
import { useCallback, useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  imageApi,
  transformApi,
  EnhancementOptions,
  NanaBananaStyle,
  TransformResult,
  EditResult,
  ImageAnalysis,
} from "@/lib/api";
import {
  Upload, ImagePlus, X, Loader2, CheckCircle2, Sparkles,
  Wand2, Download, RefreshCw, ChevronRight, Zap, Star,
  Pencil, Key, ExternalLink, AlertCircle,
} from "lucide-react";
import { ReactCompareSlider, ReactCompareSliderImage } from "react-compare-slider";

/* ─── types ────────────────────────────────────────────────────────────────── */
type ClassicResult = {
  image_id: string; status: string;
  original_url?: string; enhanced_url?: string; processing_time_ms?: number;
};

/* ─── style catalogue ───────────────────────────────────────────────────────── */
const STYLES: { id: NanaBananaStyle; emoji: string; label: string; desc: string; badge?: string }[] = [
  { id: "nano_banana",     emoji: "🍌", label: "Nano Banana",      desc: "Warm toy aesthetic, plastic glow", badge: "trending" },
  { id: "nano_banana_2",   emoji: "🍌✨",label: "Nano Banana 2",   desc: "Pastel colours, soft figurine" },
  { id: "nano_banana_pro", emoji: "🏆", label: "Nano Banana PRO",  desc: "Metallic, luxury collectible", badge: "premium" },
  { id: "product_pro",     emoji: "🛍️", label: "Product Pro",      desc: "Clean white bg, studio lighting" },
  { id: "vintage",         emoji: "📷", label: "Vintage Film",      desc: "Sepia tones, nostalgic grain" },
  { id: "cyberpunk",       emoji: "⚡", label: "Cyberpunk",         desc: "Neon blue/magenta glow" },
];

const PROMPT_PRESETS = [
  "make it bright and vivid",
  "professional product shot on white background",
  "vintage retro film look",
  "cinematic neon night vibes",
  "ultra sharp crisp detail",
  "warm golden hour lighting",
  "clean minimalist aesthetic",
  "bold vivid saturated colours",
];

const AI_EDIT_PROMPTS = [
  "make the person wear a black business suit",
  "change the background to a beach at sunset",
  "add sunglasses to the person",
  "turn this into a night scene with neon lights",
  "make the person wear a red dress",
  "change the hair colour to blonde",
  "put a crown on the person's head",
  "make the car color blue",
  "change the background to a snow mountain",
  "make the person look older",
  "add a smile to the person's face",
  "make it look like a professional headshot",
];

/* ─── component ─────────────────────────────────────────────────────────────── */
export default function EnhancePage() {
  const qc = useQueryClient();

  // shared
  const [tab, setTab] = useState<"classic" | "nano" | "edit">("edit");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  // nano banana tab
  const [style, setStyle] = useState<NanaBananaStyle>("nano_banana");
  const [prompt, setPrompt] = useState("");
  const [nanoResult, setNanoResult] = useState<TransformResult | null>(null);
  const [analysis, setAnalysis] = useState<ImageAnalysis | null>(null);
  const [analysing, setAnalysing] = useState(false);

  // ai edit tab
  const [editPrompt, setEditPrompt] = useState("");
  const [editResult, setEditResult] = useState<EditResult | null>(null);

  // provider status
  const { data: providers } = useQuery({
    queryKey: ["provider-status"],
    queryFn: () => transformApi.providerStatus().then(r => r.data),
    staleTime: 60_000,
  });
  // gradio_spaces is always available as fallback — so AI Edit always works
  const hasEditProvider = providers && (
    providers.fal_ai.available ||
    providers.huggingface.available ||
    providers.gradio_spaces?.available !== false
  );

  // classic tab
  const [options, setOptions] = useState<EnhancementOptions>({
    upscale_factor: 4, denoise: true, sharpen: true,
    color_correct: true, face_enhance: false,
    remove_background: false, output_format: "png",
  });
  const [classicResult, setClassicResult] = useState<ClassicResult | null>(null);
  const [polling, setPolling] = useState(false);

  /* ── drop zone ── */
  const onDrop = useCallback(async (accepted: File[]) => {
    const f = accepted[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setNanoResult(null);
    setClassicResult(null);
    setAnalysis(null);

    // Auto-analyse when a file is dropped
    if (tab === "nano") {
      setAnalysing(true);
      try {
        const res = await transformApi.analyze(f);
        setAnalysis(res.data);
      } catch {/* silent */} finally {
        setAnalysing(false);
      }
    }
  }, [tab]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
    maxFiles: 1, maxSize: 20 * 1024 * 1024,
  });

  /* ── ai edit mutation ── */
  const editMutation = useMutation({
    mutationFn: () => transformApi.edit(file!, editPrompt).then((r) => r.data),
    onSuccess: (data) => { setEditResult(data); qc.invalidateQueries({ queryKey: ["dashboard"] }); },
  });

  /* ── nano banana mutation ── */
  const nanoMutation = useMutation({
    mutationFn: () => transformApi.nanaBanana(file!, style, prompt).then((r) => r.data),
    onSuccess: (data) => { setNanoResult(data); qc.invalidateQueries({ queryKey: ["dashboard"] }); },
  });

  /* ── classic enhance mutation + polling ── */
  const classicMutation = useMutation({
    mutationFn: () => imageApi.upload(file!, options).then((r) => r.data),
    onSuccess: async (data) => {
      setPolling(true);
      const interval = setInterval(async () => {
        try {
          const res = await imageApi.getImage(data.image_id);
          const img = res.data;
          if (img.status === "completed" || img.status === "failed") {
            clearInterval(interval);
            setClassicResult(img);
            setPolling(false);
            qc.invalidateQueries({ queryKey: ["dashboard"] });
          }
        } catch { clearInterval(interval); setPolling(false); }
      }, 2000);
    },
  });

  const isNanoProcessing    = nanoMutation.isPending;
  const isClassicProcessing = classicMutation.isPending || polling;
  const isEditProcessing    = editMutation.isPending;
  const isProcessing = tab === "nano" ? isNanoProcessing : tab === "edit" ? isEditProcessing : isClassicProcessing;
  const resultOrigUrl = tab === "nano" ? nanoResult?.original_url : tab === "edit" ? editResult?.original_url : classicResult?.original_url;
  const resultEnhUrl  = tab === "nano" ? nanoResult?.transformed_url : tab === "edit" ? editResult?.edited_url : classicResult?.enhanced_url;
  const resultStatus  = tab === "nano" ? nanoResult?.status : tab === "edit" ? editResult?.status : classicResult?.status;

  const clearAll = () => {
    setFile(null); setPreview(null);
    setNanoResult(null); setClassicResult(null);
    setEditResult(null); setAnalysis(null);
  };

  /* ─── render ─────────────────────────────────────────────────────────────── */
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Image Studio</h1>
        <p className="text-gray-500 mt-1 text-sm">Enhance, transform, and stylise with real AI models</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
        {([
          { id: "edit",    label: "✏️ AI Edit",        },
          { id: "nano",    label: "🍌 Nano Banana",     },
          { id: "classic", label: "⚡ Classic Enhance", },
        ] as const).map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              tab === t.id
                ? "bg-white shadow text-gray-900"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* ── LEFT PANEL ── */}
        <div className="lg:col-span-2 space-y-4">

          {/* Drop zone */}
          <div
            {...getRootProps()}
            className={`relative border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              isDragActive
                ? "border-yellow-400 bg-yellow-50"
                : "border-gray-300 hover:border-yellow-400 hover:bg-yellow-50/30"
            }`}
          >
            <input {...getInputProps()} />
            {preview ? (
              <div className="relative">
                <img src={preview} alt="preview" className="w-full max-h-44 object-contain rounded-xl" />
                <button
                  onClick={(e) => { e.stopPropagation(); clearAll(); }}
                  className="absolute -top-2 -right-2 h-6 w-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <p className="mt-2 text-xs text-gray-400 truncate">{file?.name}</p>
              </div>
            ) : (
              <>
                <Upload className="h-10 w-10 text-gray-300 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-600">
                  {isDragActive ? "Drop it!" : "Drag & drop or click to upload"}
                </p>
                <p className="text-xs text-gray-400 mt-1">JPG · PNG · WebP · Max 20MB</p>
              </>
            )}
          </div>

          {/* ══ AI EDIT PANEL ══ */}
          {tab === "edit" && (
            <>
              {/* Prompt box */}
              <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
                <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                  <Pencil className="h-4 w-4 text-violet-500" />
                  What do you want to change?
                </h3>
                <textarea
                  value={editPrompt}
                  onChange={(e) => setEditPrompt(e.target.value)}
                  placeholder='e.g. "make the person wear a suit" or "change background to beach"'
                  rows={3}
                  className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-violet-400 placeholder:text-gray-300"
                />
                {/* Quick prompts */}
                <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                  {AI_EDIT_PROMPTS.map((p) => (
                    <button
                      key={p}
                      onClick={() => setEditPrompt(p)}
                      className={`text-[10px] px-2.5 py-1 rounded-full border transition-colors flex-shrink-0 ${
                        editPrompt === p
                          ? "bg-violet-100 border-violet-300 text-violet-700 font-semibold"
                          : "bg-gray-50 border-gray-200 text-gray-500 hover:bg-violet-50 hover:border-violet-200"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Provider status / setup */}
              {providers && (
                <div className={`rounded-xl border p-3 text-xs ${hasEditProvider ? "border-green-200 bg-green-50" : "border-amber-200 bg-amber-50"}`}>
                  {hasEditProvider ? (
                    <div className="flex items-center gap-2 text-green-700 font-medium">
                      <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                      {providers.fal_ai.available
                        ? `FLUX.1 Kontext ready (fal.ai) — state-of-the-art AI editing`
                        : providers.huggingface.available
                        ? `Qwen Image Edit ready (HuggingFace)`
                        : `FireRed AI Edit ready (free Gradio) — no key needed`}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-amber-700 font-semibold">
                        <AlertCircle className="h-4 w-4 flex-shrink-0" />
                        AI Edit needs a free API key to run content-level edits
                      </div>
                      <p className="text-amber-600">Add one of these free keys to <code className="bg-amber-100 px-1 rounded">.env.local</code>:</p>
                      <div className="space-y-1.5">
                        {[
                          { label: "fal.ai (best)", env: "FAL_KEY", url: "https://fal.ai/dashboard/keys", model: "FLUX.1 Kontext — makes 'person wear suit' work perfectly" },
                          { label: "HuggingFace", env: "HF_TOKEN", url: "https://huggingface.co/settings/tokens", model: "Qwen Image Edit — needs inference.serverless.write scope" },
                        ].map((p) => (
                          <div key={p.env} className="flex items-start gap-2 bg-white/60 rounded-lg px-2 py-1.5">
                            <Key className="h-3 w-3 text-amber-500 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="font-bold text-gray-700">{p.label}</span>
                                <code className="bg-gray-100 px-1 rounded text-[10px]">{p.env}=your_key</code>
                                <a href={p.url} target="_blank" rel="noopener noreferrer"
                                  className="inline-flex items-center gap-0.5 text-blue-600 hover:underline">
                                  Get free key <ExternalLink className="h-2.5 w-2.5" />
                                </a>
                              </div>
                              <div className="text-gray-400 mt-0.5">{p.model}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Edit button */}
              <button
                onClick={() => editMutation.mutate()}
                disabled={!file || !editPrompt.trim() || isEditProcessing}
                className={`w-full py-3.5 rounded-2xl font-bold text-base flex items-center justify-center gap-2 transition-all shadow-lg ${
                  !file || !editPrompt.trim() || isEditProcessing
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white"
                }`}
              >
                {isEditProcessing ? (
                  <><Loader2 className="h-5 w-5 animate-spin" /> AI is editing…</>
                ) : (
                  <><Wand2 className="h-5 w-5" /> Apply AI Edit</>
                )}
              </button>
              {editMutation.isError && (
                <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-xs text-red-600">
                  {(() => {
                    const err = editMutation.error as any;
                    const detail = err?.response?.data?.detail;
                    if (typeof detail === "object" && detail?.error === "no_provider") {
                      return (
                        <div>
                          <p className="font-bold mb-1">⚙️ No AI Edit provider configured</p>
                          <p>{detail.message}</p>
                          <p className="mt-1 text-amber-600 font-medium">{detail.fix}</p>
                        </div>
                      );
                    }
                    return <p>{typeof detail === "string" ? detail : "Edit failed. Check your API key."}</p>;
                  })()}
                </div>
              )}
            </>
          )}

          {/* ══ NANO BANANA PANEL ══ */}
          {tab === "nano" && (
            <>
              {/* Style picker */}
              <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
                <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-yellow-500" /> Choose Style
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {STYLES.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setStyle(s.id)}
                      className={`relative text-left p-3 rounded-xl border-2 transition-all ${
                        style === s.id
                          ? "border-yellow-400 bg-yellow-50 shadow-sm"
                          : "border-gray-100 hover:border-yellow-300 hover:bg-yellow-50/50"
                      }`}
                    >
                      {s.badge && (
                        <span className={`absolute top-1.5 right-1.5 text-[9px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wide ${
                          s.badge === "trending" ? "bg-orange-100 text-orange-600" : "bg-purple-100 text-purple-600"
                        }`}>
                          {s.badge}
                        </span>
                      )}
                      <div className="text-xl mb-1">{s.emoji}</div>
                      <div className="text-xs font-semibold text-gray-800">{s.label}</div>
                      <div className="text-[10px] text-gray-400 mt-0.5">{s.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt input */}
              <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
                <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                  <Wand2 className="h-4 w-4 text-violet-500" /> Prompt
                  <span className="text-[10px] font-normal text-gray-400">(optional)</span>
                </h3>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe what you want… e.g. 'bright vivid colours, white background'"
                  rows={3}
                  className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-yellow-400 placeholder:text-gray-300"
                />
                <div className="flex flex-wrap gap-1.5">
                  {PROMPT_PRESETS.slice(0, 4).map((p) => (
                    <button
                      key={p}
                      onClick={() => setPrompt(p)}
                      className="text-[10px] bg-gray-100 hover:bg-yellow-100 text-gray-600 px-2.5 py-1 rounded-full transition-colors"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              {/* Transform button */}
              <button
                onClick={() => nanoMutation.mutate()}
                disabled={!file || isNanoProcessing}
                className={`w-full py-3.5 rounded-2xl font-bold text-base flex items-center justify-center gap-2 transition-all shadow-lg ${
                  !file || isNanoProcessing
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-white"
                }`}
              >
                {isNanoProcessing ? (
                  <><Loader2 className="h-5 w-5 animate-spin" /> Transforming…</>
                ) : (
                  <><Sparkles className="h-5 w-5" /> Apply {STYLES.find(s=>s.id===style)?.label}</>
                )}
              </button>
            </>
          )}

          {/* ══ CLASSIC PANEL ══ */}
          {tab === "classic" && (
            <>
              <div className="rounded-2xl border border-gray-200 bg-white p-4 space-y-3">
                <h3 className="text-sm font-semibold text-gray-800">Enhancement Options</h3>
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1.5">Upscale</label>
                  <select
                    value={options.upscale_factor}
                    onChange={(e) => setOptions((o) => ({ ...o, upscale_factor: Number(e.target.value) }))}
                    className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-400"
                  >
                    <option value={2}>2× HD</option>
                    <option value={4}>4× Ultra HD</option>
                  </select>
                </div>
                {([
                  ["denoise", "Denoise"], ["sharpen", "Sharpen"],
                  ["color_correct", "Color Correction"],
                  ["face_enhance", "Face Restoration"],
                  ["remove_background", "Remove Background"],
                ] as [keyof EnhancementOptions, string][]).map(([key, label]) => (
                  <label key={key} className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm text-gray-700">{label}</span>
                    <button
                      type="button"
                      onClick={() => setOptions((o) => ({ ...o, [key]: !o[key] }))}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        options[key] ? "bg-brand-600" : "bg-gray-200"
                      }`}
                    >
                      <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                        options[key] ? "translate-x-4" : "translate-x-1"
                      }`} />
                    </button>
                  </label>
                ))}
                <div>
                  <label className="text-xs font-medium text-gray-600 block mb-1.5">Output Format</label>
                  <select
                    value={options.output_format}
                    onChange={(e) => setOptions((o) => ({ ...o, output_format: e.target.value as any }))}
                    className="w-full text-sm border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-400"
                  >
                    <option value="png">PNG (lossless)</option>
                    <option value="jpg">JPG (smaller)</option>
                    <option value="webp">WebP (best ratio)</option>
                  </select>
                </div>
              </div>
              <button
                onClick={() => classicMutation.mutate()}
                disabled={!file || isClassicProcessing}
                className="btn-primary w-full py-3.5 text-base"
              >
                {isClassicProcessing ? (
                  <><Loader2 className="h-5 w-5 animate-spin" />{polling ? "Enhancing…" : "Uploading…"}</>
                ) : (
                  <><Zap className="h-5 w-5" /> Enhance Now</>
                )}
              </button>
            </>
          )}
        </div>

        {/* ── RIGHT PANEL ── */}
        <div className="lg:col-span-3 space-y-4">

          {/* Result viewer */}
          {!resultStatus && !isProcessing && (
            <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 min-h-[340px] flex items-center justify-center">
              <div className="text-center px-8">
                <div className="text-5xl mb-4">{tab === "edit" ? "✏️" : tab === "nano" ? "🍌" : "⚡"}</div>
                <p className="font-semibold text-gray-600">
                  {tab === "edit" ? "AI-edited image will appear here" : "Your transformed image will appear here"}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {tab === "edit"
                    ? "Upload a photo, type what you want to change, and click Apply"
                    : "Upload a photo and choose a style to get started"}
                </p>
              </div>
            </div>
          )}

          {isProcessing && (
            <div className={`rounded-2xl border-2 border-dashed min-h-[340px] flex items-center justify-center ${
              tab === "edit" ? "border-violet-300 bg-violet-50" : "border-yellow-300 bg-yellow-50"
            }`}>
              <div className="text-center">
                <div className="relative h-16 w-16 mx-auto mb-4">
                  <div className={`absolute inset-0 rounded-full border-4 ${tab === "edit" ? "border-violet-200" : "border-yellow-200"}`} />
                  <div className={`absolute inset-0 rounded-full border-4 border-t-transparent animate-spin ${tab === "edit" ? "border-violet-500" : "border-yellow-500"}`} />
                  <div className="absolute inset-0 flex items-center justify-center text-2xl">
                    {tab === "edit" ? "✏️" : "🍌"}
                  </div>
                </div>
                <p className={`font-bold text-lg ${tab === "edit" ? "text-violet-700" : "text-yellow-700"}`}>
                  {tab === "edit" ? "FLUX.1 Kontext is editing…" : "AI is working its magic…"}
                </p>
                <p className={`text-sm mt-1 ${tab === "edit" ? "text-violet-500" : "text-yellow-600"}`}>
                  {tab === "edit"
                    ? `"${editPrompt.slice(0, 50)}${editPrompt.length > 50 ? "…" : ""}"`
                    : tab === "nano" ? `Applying ${STYLES.find(s=>s.id===style)?.label} style…` : "Enhancing with AI pipeline…"}
                </p>
                {tab === "edit" && (
                  <p className="text-xs text-violet-400 mt-2">Usually 20–60 seconds · Uses 2 credits</p>
                )}
              </div>
            </div>
          )}

          {resultStatus === "completed" && resultOrigUrl && resultEnhUrl && (
            <div className="space-y-3">
              <div className="rounded-2xl overflow-hidden shadow-xl border border-gray-100">
                <ReactCompareSlider
                  itemOne={<ReactCompareSliderImage src={resultOrigUrl} alt="Original" />}
                  itemTwo={<ReactCompareSliderImage src={resultEnhUrl} alt="Transformed" />}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-green-700">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-semibold text-sm">
                    {tab === "edit"
                      ? `AI Edit complete ✨`
                      : tab === "nano"
                      ? `${STYLES.find(s=>s.id===style)?.label} applied ✨`
                      : `Enhanced in ${((classicResult?.processing_time_ms ?? 0)/1000).toFixed(1)}s`}
                  </span>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={clearAll}
                    className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <RefreshCw className="h-4 w-4" /> New
                  </button>
                  <a
                    href={resultEnhUrl}
                    download="pixelpro-result"
                    className="btn-primary py-2 px-5 text-sm flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" /> Download
                  </a>
                </div>
              </div>
              <p className="text-xs text-gray-400 text-center">
                Drag the slider to compare Original ← → {tab === "edit" ? "AI Edited" : tab === "nano" ? "Transformed" : "Enhanced"}
              </p>
            </div>
          )}

          {resultStatus === "failed" && (
            <div className="rounded-2xl border-2 border-red-200 bg-red-50 p-8 text-center">
              <X className="h-12 w-12 text-red-300 mx-auto mb-3" />
              <p className="font-semibold text-red-700">Transform failed</p>
              <p className="text-sm text-red-500 mt-1">Your credit has been refunded.</p>
            </div>
          )}

          {/* ── "WHAT CAN HAPPEN" section ── */}
          {tab === "nano" && !nanoResult && (
            <div className="rounded-2xl border border-gray-200 bg-white p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-gray-900 text-base flex items-center gap-2">
                  <Star className="h-4 w-4 text-yellow-500" />
                  What can happen with your image?
                </h2>
                {analysing && (
                  <span className="flex items-center gap-1.5 text-xs text-yellow-600">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" /> Analysing…
                  </span>
                )}
              </div>

              {/* If no image yet — show static possibilities */}
              {!file && !analysis && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { emoji: "🍌", title: "Nano Banana Style", desc: "Become a viral collectible toy figurine", color: "yellow" },
                    { emoji: "🏆", title: "Nano Banana PRO", desc: "Metallic luxury edition with iridescent finish", color: "purple" },
                    { emoji: "🛍️", title: "Product Photography", desc: "Studio-quality e-commerce shot on white bg", color: "blue" },
                    { emoji: "📷", title: "Vintage Film", desc: "Warm sepia tones, nostalgic film grain", color: "amber" },
                    { emoji: "⚡", title: "Cyberpunk Neon", desc: "Electric neon glow, futuristic vibes", color: "cyan" },
                    { emoji: "🔍", title: "4× Super Resolution", desc: "Upscale to 4K with zero detail loss", color: "green" },
                  ].map((card) => (
                    <div
                      key={card.title}
                      className="flex items-start gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => {
                        const match = STYLES.find(s => card.title.toLowerCase().includes(s.id.replace(/_/g," ")));
                        if (match) setStyle(match.id);
                      }}
                    >
                      <span className="text-2xl">{card.emoji}</span>
                      <div>
                        <div className="text-sm font-semibold text-gray-800">{card.title}</div>
                        <div className="text-xs text-gray-400 mt-0.5">{card.desc}</div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-300 ml-auto mt-0.5 flex-shrink-0" />
                    </div>
                  ))}
                </div>
              )}

              {/* If image uploaded — show AI-personalised analysis */}
              {analysis && (
                <>
                  {/* Image stats bar */}
                  <div className="flex flex-wrap gap-2 mb-4 p-3 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-xl border border-yellow-100">
                    {[
                      ["📐", `${analysis.image_info.width}×${analysis.image_info.height}`],
                      ["🔆", analysis.image_info.is_dark ? "Dark image" : "Good brightness"],
                      ["🎯", `Sharpness ${analysis.image_info.sharpness_score.toFixed(0)}`],
                      analysis.image_info.has_faces ? ["👤", `${analysis.image_info.face_count} face(s) detected`] : ["🖼️", "No faces"],
                      analysis.image_info.is_low_resolution ? ["⚠️", "Low resolution"] : ["✅", "Good resolution"],
                    ].map(([icon, label], i) => (
                      <span key={i} className="flex items-center gap-1 text-xs bg-white px-2.5 py-1 rounded-full border border-yellow-200 text-gray-600 font-medium">
                        {icon} {label}
                      </span>
                    ))}
                  </div>

                  {/* Personalised suggestions */}
                  <div className="grid grid-cols-1 gap-2">
                    {analysis.suggestions.map((s) => (
                      <div
                        key={s.id}
                        className="flex items-center gap-3 p-3 rounded-xl hover:bg-yellow-50 border border-transparent hover:border-yellow-200 transition-all cursor-pointer group"
                        onClick={() => {
                          const styleMatch = STYLES.find(st => st.id === s.id || s.id.startsWith(st.id));
                          if (styleMatch) { setStyle(styleMatch.id); }
                          if (s.id === "denoise_sharpen") setOptions(o => ({ ...o, denoise: true, sharpen: true }));
                          if (s.id === "face_enhance") setOptions(o => ({ ...o, face_enhance: true }));
                          if (s.id === "upscale_4x") setOptions(o => ({ ...o, upscale_factor: 4 }));
                        }}
                      >
                        <span className="text-2xl">{s.icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-gray-800">{s.title}</span>
                            <div className="flex gap-1">
                              {s.tags.slice(0,2).map(t => (
                                <span key={t} className="text-[9px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{t}</span>
                              ))}
                            </div>
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5 truncate">{s.description}</p>
                        </div>
                        {/* Confidence bar */}
                        <div className="flex-shrink-0 text-right">
                          <div className="text-xs font-bold text-gray-600">{s.confidence}%</div>
                          <div className="w-12 h-1.5 bg-gray-100 rounded-full mt-1 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full"
                              style={{ width: `${s.confidence}%` }}
                            />
                          </div>
                        </div>
                        <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-yellow-500 transition-colors flex-shrink-0" />
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
