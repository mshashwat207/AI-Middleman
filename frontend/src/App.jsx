import { useState, useCallback, useRef, useEffect } from "react";
import { Link } from "react-router-dom";

const MAX_PROMPT = 32000;

const SAMPLE_PROMPT =
  "Client: Rishi Goyal, DOB: 12/03/1998, Phone: +91-9876543210, " +
  "Email: rishi@example.com, residing at 42 MG Road, Bengaluru 560001. " +
  "Aadhaar: 2345 6789 0123. PAN: ABCDE1234F. " +
  "Rishi was referred to us by the CEO of Tech Innovations, Ms. Anjali Mehta. " +
  "He is the youngest director at the firm. His husband will be joining the meeting. " +
  "Payment verified for $10,000. Account No: 9876543210. " +
  "Please draft a warm welcome email to the client.";

const ACCEPT = ".pdf,.txt,.docx,.png,.jpg,.jpeg,.tiff,.webp";

const PROVIDER_META = {
  mock:      { label: "Mock",         free: true,  note: "Simulated, no API key needed" },
  groq:      { label: "Groq",         free: true,  note: "Free tier: 14,400 req/day" },
  gemini:    { label: "Google Gemini",free: true,  note: "Free tier: 1,500 req/day" },
  openai:    { label: "OpenAI",       free: false, note: "Paid, requires billing" },
  anthropic: { label: "Anthropic",    free: false, note: "Paid, requires billing" },
};

const MODELS = {
  groq: [
    { id: "openai/gpt-oss-120b",           label: "GPT OSS 120B",           ctx: "128k" },
    { id: "openai/gpt-oss-20b",            label: "GPT OSS 20B",            ctx: "128k" },
    { id: "openai/gpt-oss-safeguard-20b",  label: "Safety GPT OSS 20B",     ctx: "128k" },
    { id: "qwen/qwen3.8-27b",              label: "Qwen 3.8 27B",           ctx: "128k" },
    { id: "allam-2-7b",                    label: "ALLaM 2 7B",             ctx: "4k" },
    { id: "meta-llama/llama-prompt-guard-2-86m", label: "Prompt Guard 2 86M", ctx: "512" },
    { id: "meta-llama/llama-prompt-guard-2-22m", label: "Prompt Guard 2 22M", ctx: "512" },
  ],
  gemini: [
    { id: "gemini-1.5-flash", label: "Gemini 1.5 Flash", ctx: "1M" },
    { id: "gemini-1.5-pro", label: "Gemini 1.5 Pro", ctx: "2M" },
  ],
  openai: [
    { id: "gpt-4o-mini", label: "GPT-4o Mini", ctx: "128k" },
    { id: "gpt-4o", label: "GPT-4o", ctx: "128k" },
  ],
  anthropic: [
    { id: "claude-3-haiku-20240307", label: "Claude 3 Haiku", ctx: "200k" },
    { id: "claude-3-5-sonnet-20240620", label: "Claude 3.5 Sonnet", ctx: "200k" },
  ]
};

const METHOD_META = [
  {
    key: "Hard Redaction",
    summary: "Replaces every detected entity with [REDACTED]. Maximum privacy, minimum utility.",
    fakeLabel: "Sent to AI",
  },
  {
    key: "Categorical Tokenization",
    summary: "Replaces entities with typed placeholders such as <PERSON_1>. Reversible via mapping.",
    fakeLabel: "Token",
  },
  {
    key: "Synthetic Swapping",
    summary: "Substitutes real values with realistic fakes via Faker. Highest semantic utility.",
    fakeLabel: "Synthetic",
  },
];

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => navigator.clipboard.writeText(text).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1800);
      })}
      className="text-2xs font-mono text-ink-400 hover:text-ink-700 transition-colors px-1.5 py-0.5"
      aria-label="Copy to clipboard"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function Tag({ children }) {
  return (
    <span className="inline-block px-1.5 py-px text-2xs font-mono font-medium tracking-wide border border-ink-300 text-ink-500">
      {children}
    </span>
  );
}

function SectionRule({ title, right }) {
  return (
    <div className="flex items-baseline gap-4 border-b border-paper-300 pb-2 mb-5">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-ink-500">{title}</h2>
      {right && <span className="ml-auto text-2xs text-ink-400">{right}</span>}
    </div>
  );
}

function CodePanel({ label, content }) {
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-2xs font-mono uppercase tracking-wider text-ink-400">{label}</span>
        <CopyButton text={content} />
      </div>
      <div className="bg-paper-200 border border-paper-300 overflow-y-auto max-h-36 p-3">
        <pre className="text-2xs font-mono text-ink-700 whitespace-pre-wrap break-words leading-relaxed">
          {content || "(empty)"}
        </pre>
      </div>
    </div>
  );
}

function UtilityBar({ score, valid }) {
  if (!valid) {
    return (
      <div className="mt-3 px-3 py-2 border border-paper-300 bg-paper-200 text-2xs text-ink-400">
        Semantic utility score not available for simulated responses. Use a real provider.
      </div>
    );
  }
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? "bg-success" : pct >= 50 ? "bg-warn" : "bg-danger";
  const textColor = pct >= 80 ? "text-success" : pct >= 50 ? "text-warn" : "text-danger";
  return (
    <div className="mt-3 flex flex-col gap-1">
      <div className="flex items-center justify-between text-2xs">
        <span className="text-ink-400 uppercase tracking-wider font-semibold">Semantic utility</span>
        <span className={`font-mono font-semibold ${textColor}`}>{pct}%</span>
      </div>
      <div
        className="h-1.5 w-full bg-paper-300"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Semantic utility score"
      >
        <div className={`h-full transition-all duration-300 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-2xs text-ink-400">
        Cosine similarity of re-hydrated output vs original prompt
      </p>
    </div>
  );
}

const CATEGORY_LABELS = {
  ROLE_IDENTITY:           "Role identity",
  SUPERLATIVE_IDENTITY:    "Superlative identity",
  RELATIONAL_REFERENCE:    "Relational reference",
  LOCATOR_REFERENCE:       "Locator reference",
  QUASI_IDENTIFIER_CLUSTER:"Quasi-identifier cluster",
};

function IndirectPIIWarnings({ warnings }) {
  if (!warnings || warnings.length === 0) return null;
  return (
    <section aria-label="Indirect PII warnings">
      <SectionRule title="Indirect PII" right={`${warnings.length} warning${warnings.length > 1 ? "s" : ""}`} />
      <div className="flex flex-col gap-0">
        {warnings.map((w, i) => (
          <div key={i} className="border border-warn/30 bg-warn/5 px-4 py-3 border-b-0 last:border-b">
            <div className="flex items-baseline gap-2 flex-wrap">
              <span className="text-xs font-semibold text-warn">
                {CATEGORY_LABELS[w.category] ?? w.category}
              </span>
              <code className="text-2xs font-mono text-ink-700 bg-paper-200 px-1.5 py-px border border-paper-300 max-w-xs truncate" title={w.snippet}>
                {w.snippet}
              </code>
            </div>
            <p className="text-xs text-ink-500 mt-1 leading-relaxed">{w.reason}</p>
          </div>
        ))}
      </div>
      <p className="text-2xs text-ink-400 mt-2">
        These patterns were detected locally without sending data to any AI. They indicate text that
        could identify a person through world knowledge or context, even though no direct PII
        like a name or phone number is present. Review before proceeding.
      </p>
    </section>
  );
}

function EntityTable({ table, fakeLabel }) {
  if (!table || table.length === 0) return null;
  return (
    <div className="mt-3 border border-paper-300 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-1.5 bg-paper-200 border-b border-paper-300">
        <span className="text-2xs font-mono uppercase tracking-wider text-ink-500">
          Original vs {fakeLabel}
        </span>
        <span className="text-2xs text-ink-400">{table.length} entities</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-2xs">
          <thead>
            <tr className="border-b border-paper-300 bg-paper-100">
              <th className="px-3 py-1.5 text-left font-semibold text-ink-500 whitespace-nowrap">Type</th>
              <th className="px-3 py-1.5 text-left font-semibold text-ink-500 whitespace-nowrap">Original</th>
              <th className="px-3 py-1.5 text-left font-semibold text-ink-500 whitespace-nowrap">Sent to AI</th>
              <th className="px-3 py-1.5 text-left font-semibold text-ink-500 whitespace-nowrap">Conf.</th>
            </tr>
          </thead>
          <tbody>
            {table.map((row, i) => (
              <tr key={i} className="border-b border-paper-200 last:border-0">
                <td className="px-3 py-1.5"><Tag>{row.entity_type}</Tag></td>
                <td className="px-3 py-1.5 font-mono text-danger max-w-[9rem] truncate" title={row.real_value}>{row.real_value}</td>
                <td className="px-3 py-1.5 font-mono text-accent max-w-[9rem] truncate" title={row.fake_value}>{row.fake_value}</td>
                <td className="px-3 py-1.5 font-mono text-ink-400">{(row.confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MethodCard({ meta, result, loading }) {
  return (
    <div className="flex flex-col bg-paper-50 border border-paper-300 p-5 animate-fade-in">
      <div className="flex items-start justify-between gap-2 mb-1">
        <h3 className="text-sm font-semibold text-ink-900">{meta.key}</h3>
        <div className="flex items-center gap-2 shrink-0">
          {result && (
            <>
              <span className="text-2xs font-mono text-ink-400 border border-paper-300 px-1.5 py-px">
                {result.entities_found} entities
              </span>
              <span className="text-2xs font-mono text-ink-400 border border-paper-300 px-1.5 py-px">
                {result.latency_ms.toFixed(0)} ms
              </span>
              <span className="text-2xs font-mono text-ink-400 border border-paper-300 px-1.5 py-px">
                {result.response_length} chars
              </span>
            </>
          )}
        </div>
      </div>
      <p className="text-xs text-ink-500 leading-relaxed mb-3">{meta.summary}</p>

      {loading && (
        <div className="flex flex-col gap-2">
          {[80, 64, 80].map((h, i) => (
            <div key={i} className="bg-paper-200 animate-pulse" style={{ height: `${h}px` }} aria-hidden="true" />
          ))}
        </div>
      )}

      {result && !loading && (
        <>
          <UtilityBar score={result.utility_score} valid={result.utility_score_valid} />
          <EntityTable table={result.entity_table} fakeLabel={meta.fakeLabel} />
          <CodePanel label="Masked payload sent to AI" content={result.masked_payload} />
          <CodePanel label="Raw AI response" content={result.llm_response} />
          <CodePanel label="Re-hydrated output" content={result.final_unmasked_output} />
          {result.entity_types.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {result.entity_types.map((t) => <Tag key={t}>{t}</Tag>)}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function FirewallStatus({ firewall }) {
  if (!firewall) {
    return (
      <div className="flex items-center gap-2 py-2 text-xs text-ink-400">
        <span className="inline-block w-2 h-2 rounded-full bg-ink-300" aria-hidden="true" />
        Firewall standing by. Submit a prompt to scan.
      </div>
    );
  }
  const passed = firewall.passed !== false;
  return (
    <div
      role="status"
      aria-live="polite"
      className={`flex items-start gap-3 border px-4 py-3 animate-fade-in text-sm ${
        passed ? "border-paper-300 bg-paper-100 text-ink-700" : "border-danger/30 bg-danger/5 text-danger"
      }`}
    >
      <span className={`mt-0.5 inline-block w-2 h-2 rounded-full shrink-0 ${passed ? "bg-success" : "bg-danger"}`} aria-hidden="true" />
      <div className="min-w-0">
        <span className="font-semibold">Injection scan: {passed ? "Clear" : "Blocked"}</span>
        {firewall.risk_score > 0 && (
          <span className="ml-2 font-mono text-xs text-ink-400">risk {(firewall.risk_score * 100).toFixed(0)}%</span>
        )}
        {firewall.detected_patterns?.length > 0 && (
          <p className="mt-1 text-xs text-ink-500">Patterns: {firewall.detected_patterns.join(", ")}</p>
        )}
        {passed && !firewall.detected_patterns?.length && (
          <p className="mt-0.5 text-xs text-ink-400">No injection patterns detected.</p>
        )}
      </div>
    </div>
  );
}

function LengthBar({ length, limit }) {
  const pct = Math.min((length / limit) * 100, 100);
  const barColor = pct > 90 ? "bg-danger" : pct > 70 ? "bg-warn" : "bg-accent";
  const textColor = pct > 90 ? "text-danger" : pct > 70 ? "text-warn" : "text-ink-400";
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-2xs">
        <span className="text-ink-400">Characters</span>
        <span className={`font-mono ${textColor}`}>{length.toLocaleString()} / {limit.toLocaleString()}</span>
      </div>
      <div className="h-px w-full bg-paper-300 overflow-hidden" role="progressbar" aria-valuenow={length} aria-valuemin={0} aria-valuemax={limit} aria-label="Prompt length">
        <div className={`h-full transition-all duration-200 ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function DropZone({ onFile, dragging, setDragging }) {
  const inputRef = useRef(null);
  const processFile = useCallback((file) => { if (file) onFile(file); }, [onFile]);
  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Upload file, click or drag and drop"
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); processFile(e.dataTransfer.files[0]); }}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
      className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed px-6 py-10 cursor-pointer transition-colors ${
        dragging ? "border-accent bg-accent/5" : "border-paper-300 bg-paper-100 hover:border-ink-400"
      }`}
    >
      <svg className="w-6 h-6 text-ink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
      <div className="text-center">
        <p className={`text-sm font-medium transition-colors ${dragging ? "text-accent" : "text-ink-700"}`}>
          {dragging ? "Release to upload" : "Drop a file or click to browse"}
        </p>
        <p className="text-xs text-ink-400 mt-0.5">PDF, DOCX, TXT, PNG, JPG, max 20 MB</p>
      </div>
      <input ref={inputRef} type="file" accept={ACCEPT} className="sr-only" aria-hidden="true" onChange={(e) => processFile(e.target.files[0])} />
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xl font-serif font-semibold text-ink-900 tabular-nums">{value}</span>
      <span className="text-2xs text-ink-400 uppercase tracking-wider">{label}</span>
    </div>
  );
}

function ErrorMessage({ message }) {
  return (
    <div role="alert" className="flex items-start gap-2 px-4 py-3 border border-danger/30 bg-danger/5 text-danger text-sm animate-fade-in">
      <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      {message}
    </div>
  );
}

function ProviderBadge({ providerUsed, modelUsed, isSimulated }) {
  const meta = PROVIDER_META[providerUsed] ?? { label: providerUsed, free: false };
  return (
    <div className={`flex items-center gap-2 px-3 py-2 border text-xs font-mono ${
      isSimulated ? "border-warn/30 bg-warn/5 text-warn" : "border-success/30 bg-success/5 text-success"
    }`}>
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${isSimulated ? "bg-warn" : "bg-success"}`} aria-hidden="true" />
      {isSimulated
        ? "Simulated responses. Connect a real provider for meaningful results."
        : `${meta.label} / ${modelUsed}`
      }
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState("text");
  const [prompt, setPrompt] = useState(SAMPLE_PROMPT);
  const [pendingFile, setPendingFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [modelOverride, setModelOverride] = useState("gemini-1.5-flash");
  const [temperature, setTemperature] = useState(0.7);
  const [enforceFirewall, setEnforceFirewall] = useState(false);
  const [kThreshold, setKThreshold] = useState(3);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const fetchHistory = useCallback(() => {
    fetch((import.meta.env.VITE_API_URL || "") + "/api/history?limit=20")
      .then((r) => r.json())
      .then((d) => setHistory(d.entries || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch((import.meta.env.VITE_API_URL || "") + "/api/providers")
      .then((r) => r.json())
      .then((d) => {
        if (d.providers) {
          setProviders(d.providers);
          const first = d.providers.find((p) => p.configured && p.name !== "mock");
          if (first) {
            setSelectedProvider(first.name);
            setModelOverride(first.default_model || "");
          }
        }
      })
      .catch(() => {});
  }, []);

  const handleProviderChange = (e) => {
    const name = e.target.value;
    setSelectedProvider(name);
    const found = providers.find((p) => p.name === name);
    setModelOverride(found?.default_model || "");
  };

  const handlePromptChange = (e) => { setPrompt(e.target.value); setError(null); setData(null); };
  const handleFileSelect = useCallback((file) => { setPendingFile(file); setError(null); setData(null); }, []);
  const clearFile = () => { setPendingFile(null); setData(null); setError(null); };

  const exportJSON = useCallback(() => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `vul-llm-${data.request_id?.slice(0, 8) ?? "result"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  const runBenchmark = useCallback(async () => {
    setLoading(true);
    setError(null);
    setData(null);

    try {
      let res;
      if (mode === "file" && pendingFile) {
        const form = new FormData();
        form.append("file", pendingFile);
        form.append("provider", selectedProvider);
        form.append("temperature", String(temperature));
        form.append("enforce_firewall", enforceFirewall);
        form.append("k_threshold", kThreshold);
        if (modelOverride) form.append("model_name", modelOverride);
        res = await fetch((import.meta.env.VITE_API_URL || "") + "/api/upload-benchmark", { method: "POST", body: form });
      } else {
        const trimmed = prompt.trim();
        if (!trimmed) { setError("Prompt cannot be empty."); setLoading(false); return; }
        if (trimmed.length > MAX_PROMPT) { setError(`Prompt exceeds ${MAX_PROMPT.toLocaleString()} character limit.`); setLoading(false); return; }
        res = await fetch((import.meta.env.VITE_API_URL || "") + "/api/benchmark", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            prompt: trimmed, 
            provider: selectedProvider, 
            model_name: modelOverride || null, 
            temperature,
            enforce_firewall: enforceFirewall,
            k_threshold: kThreshold
          }),
        });
      }

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        if (res.status === 403) {
          setData({
            firewall: { passed: false, risk_score: 1.0, detected_patterns: body.detail ? [body.detail] : ["blocked"] },
            results: [], total_latency_ms: 0,
            original_prompt: mode === "text" ? prompt : "",
            request_id: null, file_info: null,
            prompt_length: 0, prompt_length_limit: MAX_PROMPT,
            provider_used: selectedProvider, model_used: modelOverride || "", is_simulated: true,
          });
          return;
        }
        throw new Error(body.detail || `HTTP ${res.status}`);
      }

      setData(await res.json());
    } catch (err) {
      setError(err.message || "Unexpected error. Is the backend running on port 8000?");
    } finally {
      setLoading(false);
    }
  }, [mode, prompt, pendingFile, selectedProvider, modelOverride, temperature, enforceFirewall, kThreshold]);

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runBenchmark();
  };

  const selectedProviderInfo = providers.find((p) => p.name === selectedProvider);
  const providerConfigured = selectedProviderInfo?.configured ?? (selectedProvider === "mock");
  const canRun = !loading && (mode === "text" ? prompt.trim().length > 0 : !!pendingFile);
  const totalEntities = data?.results?.[0]?.entities_found ?? 0;
  const latency = data?.total_latency_ms ? `${data.total_latency_ms.toFixed(0)} ms` : null;

  return (
    <div className="min-h-screen bg-paper-100 text-ink-900">
      <header className="sticky top-0 z-10 bg-paper-100 border-b border-paper-300">
        <div className="max-w-content mx-auto px-6 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="font-serif font-semibold text-base text-ink-900 tracking-tight">VUL-LLM</span>
            <span className="hidden sm:inline text-ink-300 select-none">|</span>
            <span className="hidden sm:inline text-xs text-ink-500">PII Masking Benchmark</span>
          </div>
          <nav className="flex items-center gap-5 text-xs text-ink-500">
            <button
              type="button"
              onClick={() => { fetchHistory(); setShowHistory((v) => !v); }}
              className="hover:text-ink-900 transition-colors"
            >
              {showHistory ? "Hide history" : "History"}
            </button>
            <Link to="/privacy" className="hover:text-ink-900 transition-colors">Privacy</Link>
            <Link to="/terms" className="hover:text-ink-900 transition-colors">Terms</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-content mx-auto px-6 py-12 flex flex-col gap-12">

        <section className="max-w-2xl">
          <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-ink-900 leading-tight tracking-tight">
            How much does privacy cost?
          </h1>
          <p className="mt-4 text-base text-ink-500 leading-relaxed">
            VUL-LLM runs your document through three masking methods simultaneously
            and shows what each one sends to the AI, what comes back, and what
            gets returned to you. A semantic utility score measures how much
            meaning each method preserves.
          </p>
        </section>

        <section aria-label="Benchmark input">
          <SectionRule title="Input" />

          <div role="tablist" aria-label="Input method" className="flex gap-0 mb-5 border border-paper-300 w-fit">
            {[{ id: "text", label: "Text" }, { id: "file", label: "File upload" }].map(({ id, label }) => (
              <button
                key={id}
                role="tab"
                aria-selected={mode === id}
                onClick={() => { setMode(id); setError(null); setData(null); }}
                className={`px-4 py-1.5 text-sm transition-colors ${
                  mode === id ? "bg-ink-900 text-paper-100" : "bg-paper-100 text-ink-500 hover:text-ink-900"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {mode === "text" && (
            <div className="flex flex-col gap-2">
              <div className="flex items-baseline justify-between mb-1">
                <label htmlFor="prompt-input" className="text-xs text-ink-500">
                  Paste a document with personal data. Medical, legal, and financial text work well.
                </label>
                <button
                  type="button"
                  onClick={() => { setPrompt(SAMPLE_PROMPT); setError(null); setData(null); }}
                  className="text-xs text-accent hover:underline ml-4 shrink-0"
                >
                  Load sample
                </button>
              </div>
              <textarea
                id="prompt-input"
                value={prompt}
                onChange={handlePromptChange}
                onKeyDown={handleKeyDown}
                rows={7}
                maxLength={MAX_PROMPT}
                spellCheck={false}
                placeholder="Patient: Priya Sharma, DOB: 05/11/1985, Phone: +91-9123456789..."
                aria-label="Prompt text"
                className="w-full resize-y border border-paper-300 bg-paper-50 px-4 py-3 text-sm font-mono text-ink-800 placeholder:text-ink-300 focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent transition-colors"
              />
              <LengthBar length={prompt.length} limit={MAX_PROMPT} />
            </div>
          )}

          {mode === "file" && (
            <div className="flex flex-col gap-3">
              {!pendingFile ? (
                <DropZone onFile={handleFileSelect} dragging={dragging} setDragging={setDragging} />
              ) : (
                <div className="flex items-center gap-3 px-4 py-3 border border-paper-300 bg-paper-50">
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-ink-900 truncate block">{pendingFile.name}</span>
                    <span className="text-xs text-ink-400">{(pendingFile.size / 1024).toFixed(1)} KB, ready to scan</span>
                  </div>
                  <button type="button" onClick={clearFile} aria-label="Remove file" className="text-ink-400 hover:text-ink-900 transition-colors p-1">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              )}
              <p className="text-xs text-ink-400">Supports PDF, DOCX, TXT, and images (OCR). Truncated to 32,000 characters.</p>
            </div>
          )}

          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div className="flex flex-col gap-1">
              <label htmlFor="provider-select" className="text-xs text-ink-500">AI provider</label>
              <select
                id="provider-select"
                value={selectedProvider}
                onChange={handleProviderChange}
                className="border border-paper-300 bg-paper-50 px-3 py-1.5 text-sm text-ink-800 focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent"
              >
                {(providers.length > 0 ? providers : Object.entries(PROVIDER_META).map(([name, m]) => ({ name, configured: name === "mock", default_model: "", free: m.free }))).map((p) => (
                  <option key={p.name} value={p.name} disabled={!p.configured}>
                    {PROVIDER_META[p.name]?.label ?? p.name}
                    {PROVIDER_META[p.name]?.free ? " (free)" : " (paid)"}
                    {!p.configured ? " no key" : ""}
                  </option>
                ))}
              </select>
              {selectedProviderInfo && (
                <p className="text-2xs text-ink-400">{PROVIDER_META[selectedProvider]?.note}</p>
              )}
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="model-input" className="text-xs text-ink-500">Model</label>
              {MODELS[selectedProvider] ? (
                <select
                  id="model-input"
                  value={modelOverride}
                  onChange={(e) => setModelOverride(e.target.value)}
                  aria-label={`${selectedProvider} model`}
                  className="border border-paper-300 bg-paper-50 px-3 py-1.5 text-sm font-mono text-ink-800 focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent"
                >
                  {MODELS[selectedProvider].map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label} ({m.ctx})
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  id="model-input"
                  type="text"
                  value={modelOverride}
                  onChange={(e) => setModelOverride(e.target.value)}
                  placeholder={selectedProviderInfo?.default_model || "default"}
                  disabled={selectedProvider === "mock"}
                  aria-label="Model name"
                  className="border border-paper-300 bg-paper-50 px-3 py-1.5 text-sm font-mono text-ink-800 placeholder:text-ink-300 focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent disabled:opacity-40 disabled:cursor-not-allowed"
                />
              )}
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor="temperature-slider" className="text-xs text-ink-500">
                Temperature <span className="font-mono">{temperature.toFixed(1)}</span>
              </label>
              <input
                id="temperature-slider"
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                disabled={selectedProvider === "mock"}
                aria-label="Temperature"
                className="w-full accent-accent disabled:opacity-40"
              />
              <div className="flex justify-between text-2xs text-ink-300">
                <span>0.0 precise</span>
                <span>1.0 creative</span>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <label htmlFor="firewall-toggle" className="text-xs text-ink-500">Enforce Firewall</label>
                <input
                  id="firewall-toggle"
                  type="checkbox"
                  checked={enforceFirewall}
                  onChange={(e) => setEnforceFirewall(e.target.checked)}
                  className="accent-accent"
                />
              </div>
              <div className="flex items-center justify-between mt-1">
                <label htmlFor="k-slider" className="text-xs text-ink-500">
                  K-Threshold: <span className="font-mono">{kThreshold}</span>
                </label>
              </div>
              <input
                id="k-slider"
                type="range"
                min="1"
                max="5"
                step="1"
                value={kThreshold}
                onChange={(e) => setKThreshold(parseInt(e.target.value, 10))}
                disabled={!enforceFirewall}
                aria-label="K-Threshold"
                className="w-full accent-accent disabled:opacity-40"
              />
              <div className="flex justify-between text-2xs text-ink-300">
                <span>1 (Strict)</span>
                <span>5 (Loose)</span>
              </div>
            </div>

            {!providerConfigured && selectedProvider !== "mock" && (
              <p className="text-xs text-danger pb-1.5">
                Set <code className="font-mono">{selectedProvider.toUpperCase()}_API_KEY</code> in .env
              </p>
            )}
          </div>

          {error && <div className="mt-3"><ErrorMessage message={error} /></div>}

          <div className="mt-4 flex items-center gap-4 flex-wrap">
            <button
              type="button"
              onClick={runBenchmark}
              disabled={!canRun || (!providerConfigured && selectedProvider !== "mock")}
              className="px-5 py-2 text-sm font-medium bg-ink-900 text-paper-50 hover:bg-ink-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent"
            >
              {loading ? (mode === "file" ? "Extracting..." : "Running...") : "Run benchmark"}
            </button>
            {data && (
              <button
                type="button"
                onClick={exportJSON}
                className="px-4 py-2 text-sm font-medium border border-paper-300 text-ink-700 hover:bg-paper-200 transition-colors focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent"
              >
                Export JSON
              </button>
            )}
            <span className="text-xs text-ink-400 select-none">
              {typeof navigator !== "undefined" && navigator.platform?.includes("Mac") ? "Cmd + Return" : "Ctrl + Enter"}
            </span>
          </div>
        </section>

        <section aria-label="Injection firewall status">
          <SectionRule title="Firewall" />
          <FirewallStatus firewall={data?.firewall ?? null} />
        </section>

        {data?.indirect_pii_warnings && (
          <IndirectPIIWarnings warnings={data.indirect_pii_warnings} />
        )}

        {data?.file_info && (
          <section aria-label="File analysis">
            <SectionRule title="File" />
            <div className="flex items-start gap-4 px-4 py-3 border border-paper-300 bg-paper-50">
              <div className="flex-1 min-w-0">
                <span className="text-sm font-medium text-ink-900">{data.file_info.filename}</span>
                <span className="ml-2 text-2xs font-mono border border-ink-300 text-ink-500 px-1.5 py-px">{data.file_info.file_type}</span>
                <p className="text-xs text-ink-400 mt-0.5">
                  {(data.file_info.size_bytes / 1024).toFixed(1)} KB, {data.file_info.extracted_chars.toLocaleString()} characters extracted
                </p>
              </div>
            </div>
            <div className="mt-3">
              <LengthBar length={data.prompt_length} limit={data.prompt_length_limit} />
            </div>
          </section>
        )}

        {(data?.results?.length > 0 || loading) && (
          <section aria-label="3-way masking comparison">
            <SectionRule
              title="Comparison"
              right={data ? `${totalEntities} entities, ${latency ?? ""}` : undefined}
            />

            {data && (
              <div className="flex flex-col gap-3 mb-6">
                <ProviderBadge
                  providerUsed={data.provider_used}
                  modelUsed={data.model_used}
                  isSimulated={data.is_simulated}
                />
                <div className="flex gap-8 flex-wrap">
                  <Stat label="PII entities" value={totalEntities} />
                  {latency && <Stat label="Total latency" value={latency} />}
                  <Stat label="Pipelines" value="3" />
                  <Stat label="Temperature" value={temperature.toFixed(1)} />
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-paper-300">
              {METHOD_META.map((meta) => (
                <MethodCard
                  key={meta.key}
                  meta={meta}
                  result={data?.results?.find((r) => r.method === meta.key) ?? null}
                  loading={loading}
                />
              ))}
            </div>
          </section>
        )}

        {data?.results?.length > 0 && (
          <section aria-label="Original content">
            <SectionRule title="Original content" />
            <div className="border border-paper-300 bg-paper-50 p-4">
              <pre className="text-2xs font-mono text-ink-500 whitespace-pre-wrap break-words leading-relaxed max-h-40 overflow-y-auto">
                {data.original_prompt}
              </pre>
              {data.request_id && (
                <p className="mt-3 pt-3 border-t border-paper-200 text-2xs font-mono text-ink-300">{data.request_id}</p>
              )}
            </div>
          </section>
        )}
      </main>

      {showHistory && (
        <div className="max-w-content mx-auto px-6 py-8">
          <div className="flex items-center gap-4 border-b border-paper-300 pb-2 mb-5">
            <h2 className="text-xs font-semibold uppercase tracking-widest text-ink-500">Request history</h2>
            <span className="ml-auto text-2xs text-ink-400">{history.length} recent</span>
            <button
              type="button"
              onClick={fetchHistory}
              className="text-2xs text-accent hover:underline"
            >
              Refresh
            </button>
          </div>
          {history.length === 0 ? (
            <p className="text-sm text-ink-400">No requests recorded yet. Run a benchmark first.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-2xs border border-paper-300">
                <thead>
                  <tr className="bg-paper-200 border-b border-paper-300">
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Time</th>
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Provider</th>
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Model</th>
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Entities</th>
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Risk</th>
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Latency</th>
                    <th className="px-3 py-2 text-left font-semibold text-ink-500 whitespace-nowrap">Blocked</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((row, i) => (
                    <tr key={i} className="border-b border-paper-200 last:border-0 hover:bg-paper-100">
                      <td className="px-3 py-2 font-mono text-ink-500 whitespace-nowrap">
                        {row.created_at ? new Date(row.created_at).toLocaleTimeString() : "—"}
                      </td>
                      <td className="px-3 py-2 text-ink-700">{row.provider}</td>
                      <td className="px-3 py-2 font-mono text-ink-500 max-w-[8rem] truncate">{row.model}</td>
                      <td className="px-3 py-2 text-ink-700">{row.pii_entity_count}</td>
                      <td className="px-3 py-2 font-mono text-ink-500">
                        {row.prompt_risk_score != null ? (row.prompt_risk_score * 100).toFixed(0) + "%" : "—"}
                      </td>
                      <td className="px-3 py-2 font-mono text-ink-500">
                        {row.latency_ms != null ? row.latency_ms.toFixed(0) + " ms" : "—"}
                      </td>
                      <td className="px-3 py-2">
                        {row.blocked
                          ? <span className="text-danger font-semibold">Yes</span>
                          : <span className="text-success">No</span>
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <footer className="border-t border-paper-300 mt-16">
        <div className="max-w-content mx-auto px-6 py-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <p className="text-xs text-ink-400">
            VUL-LLM is a research prototype released under the MIT Licence.
            {data?.is_simulated ? " Results above are simulated." : ""}
          </p>
          <nav className="flex items-center gap-4 text-xs text-ink-400">
            <Link to="/privacy" className="hover:text-ink-900 transition-colors">Privacy policy</Link>
            <Link to="/terms" className="hover:text-ink-900 transition-colors">Terms of use</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
