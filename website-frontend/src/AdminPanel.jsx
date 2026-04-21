import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertCircle,
  BarChart3,
  Bot,
  Download,
  ExternalLink,
  MoonStar,
  RefreshCw,
  Radio,
  Send,
  Shield,
  Sparkles,
  SunMedium,
  Users,
} from 'lucide-react';

const WINDOW_OPTIONS = [
  { label: '5m', value: '5m' },
  { label: '30m', value: '30m' },
  { label: '2h', value: '2h' },
];

const PREMIUM_ACTION_OPTIONS = [
  { value: 'add', label: 'Add premium' },
  { value: 'lifetime', label: 'Set lifetime' },
  { value: 'remove', label: 'Remove premium' },
];

const PAGE_SIZE_OPTIONS = [25, 50, 100, 200];

const BROADCAST_AUDIENCE_OPTIONS = [
  { value: 'all', label: 'All users' },
  { value: 'premium', label: 'Premium' },
  { value: 'verified', label: 'Verified' },
  { value: 'non_verified', label: 'Non-verified' },
];

const EMPTY_FILTERS = {
  symbol: '',
  reject_reason: '',
  status: '',
  tier: '',
  engine: '',
  regime: '',
};

const ADMIN_THEME_STORAGE_KEY = 'cm_admin_dark_mode';

const readError = async (resp, fallback = 'Request failed') => {
  if (!resp) return fallback;
  try {
    const data = await resp.clone().json();
    const msg = data?.detail || data?.message || data?.error;
    if (typeof msg === 'string' && msg.trim()) return msg.trim();
  } catch {}
  try {
    const text = (await resp.text()).trim();
    if (text) return text;
  } catch {}
  return fallback;
};

const fmtNumber = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '0';
  return Intl.NumberFormat('en-US').format(n);
};

const fmtScore = (value) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '-';
  return n.toFixed(3);
};

const humanWindow = (windowKey) => {
  const match = WINDOW_OPTIONS.find((item) => item.value === windowKey);
  return match?.label || '30m';
};

export function AdminDeniedScreen({ user, onLogout }) {
  return (
    <div className="min-h-screen bg-[#0a0806] text-stone-100 flex items-center justify-center px-4">
      <div className="max-w-xl w-full rounded-[2rem] border border-rose-500/20 bg-[radial-gradient(circle_at_top,#402217_0%,#150d0a_55%,#090807_100%)] p-8 shadow-[0_20px_80px_rgba(0,0,0,0.5)]">
        <div className="flex items-center gap-3 text-rose-300">
          <Shield className="w-7 h-7" />
          <p className="text-xs uppercase tracking-[0.35em] font-black">Admin Access Required</p>
        </div>
        <h1 className="mt-5 text-3xl font-black text-white">This route is reserved for Telegram admins.</h1>
        <p className="mt-4 text-sm leading-7 text-stone-300">
          You are signed in{user?.first_name ? ` as ${user.first_name}` : ''}, but your Telegram ID is not in the admin allowlist.
          The trading dashboard is still available on the standard app route.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href="/"
            className="rounded-full border border-stone-300/15 bg-white/5 px-5 py-3 text-sm font-bold text-stone-100 transition hover:bg-white/10"
          >
            Open User Dashboard
          </a>
          <button
            onClick={onLogout}
            className="rounded-full border border-rose-400/25 bg-rose-500/10 px-5 py-3 text-sm font-bold text-rose-200 transition hover:bg-rose-500/20"
          >
            Disconnect
          </button>
        </div>
      </div>
    </div>
  );
}

function SectionShell({ eyebrow, title, action, children, className = '' }) {
  return (
    <section className={`relative overflow-hidden rounded-[2rem] border border-[color:var(--panel-border)] bg-[var(--panel-bg)] p-6 shadow-[var(--panel-shadow)] backdrop-blur-2xl ${className}`}>
      <div className="absolute inset-0 bg-[var(--panel-gloss)] pointer-events-none" />
      <div className="relative z-10 flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.35em] text-[var(--accent-text)]">{eyebrow}</p>
          <h2 className="mt-3 text-xl font-black tracking-tight text-[var(--text-main)]">{title}</h2>
        </div>
        {action}
      </div>
      <div className="relative z-10 mt-6">{children}</div>
    </section>
  );
}

function OverviewCard({ label, value, accent, note }) {
  return (
    <div className="rounded-[1.5rem] border border-[color:var(--soft-border)] bg-[var(--card-bg)] p-4">
      <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--text-dim)]">{label}</p>
      <div className={`mt-3 text-3xl font-black ${accent}`}>{value}</div>
      {note ? <p className="mt-2 text-xs text-[var(--text-muted)]">{note}</p> : null}
    </div>
  );
}

function Badge({ children, tone = 'neutral' }) {
  const tones = {
    neutral: 'border-[color:var(--soft-border)] bg-[var(--badge-neutral-bg)] text-[var(--text-soft)]',
    green: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-200',
    amber: 'border-[color:var(--accent-border)] bg-[var(--accent-soft-bg)] text-[var(--accent-soft-text)]',
    rose: 'border-rose-500/25 bg-rose-500/10 text-rose-200',
    cyan: 'border-cyan-500/25 bg-cyan-500/10 text-cyan-100',
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-bold ${tones[tone] || tones.neutral}`}>
      {children}
    </span>
  );
}

function ConfirmModal({ title, description, confirmLabel, tone = 'amber', onCancel, onConfirm, busy }) {
  const tones = {
    amber: 'border-amber-400/35 bg-amber-500/15 text-amber-100 hover:bg-amber-500/25',
    rose: 'border-rose-400/35 bg-rose-500/15 text-rose-100 hover:bg-rose-500/25',
    cyan: 'border-cyan-400/35 bg-cyan-500/15 text-cyan-100 hover:bg-cyan-500/25',
  };
  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/65 px-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-[2rem] border border-[color:var(--panel-border)] bg-[var(--panel-bg-strong)] p-6 shadow-[var(--panel-shadow)]">
        <p className="text-[11px] uppercase tracking-[0.35em] text-[var(--accent-text)]">Confirm Action</p>
        <h3 className="mt-3 text-2xl font-black text-[var(--text-main)]">{title}</h3>
        <p className="mt-3 text-sm leading-7 text-[var(--text-muted)]">{description}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onCancel} disabled={busy} className="rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-4 py-2 text-sm font-bold text-[var(--text-soft)] hover:bg-[var(--button-muted-hover)] disabled:opacity-50">
            Cancel
          </button>
          <button onClick={onConfirm} disabled={busy} className={`rounded-full border px-4 py-2 text-sm font-bold disabled:opacity-50 ${tones[tone] || tones.amber}`}>
            {busy ? 'Working...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

function ChipSelector({ options, value, onChange, tone = 'neutral', compact = false }) {
  const activeTone = {
    neutral: 'border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] text-[var(--text-main)]',
    amber: 'border-[#c7a56b]/30 bg-[#c7a56b]/15 text-[#f2ddb0]',
    cyan: 'border-cyan-400/25 bg-cyan-500/12 text-cyan-100',
    rose: 'border-rose-400/25 bg-rose-500/12 text-rose-100',
  };
  return (
    <div className={`flex flex-wrap gap-2 rounded-[1.4rem] border border-[color:var(--soft-border)] bg-[var(--card-bg)] ${compact ? 'p-1.5' : 'p-2'}`}>
      {options.map((option) => {
        const optValue = option.value ?? option;
        const optLabel = option.label ?? String(option);
        const isActive = value === optValue;
        return (
          <button
            key={String(optValue)}
            type="button"
            onClick={() => onChange(optValue)}
            className={`rounded-full border px-4 py-2 text-xs font-bold transition ${
              isActive
                ? (activeTone[tone] || activeTone.neutral)
                : 'border-[color:var(--soft-border)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:bg-[var(--button-muted-hover)]'
            }`}
          >
            {optLabel}
          </button>
        );
      })}
    </div>
  );
}

export default function AdminPanel({ user, apiFetch, onLogout }) {
  const [isDarkMode, setIsDarkMode] = useState(() => {
    try {
      const raw = localStorage.getItem(ADMIN_THEME_STORAGE_KEY);
      if (raw === 'light') return false;
      if (raw === 'dark') return true;
    } catch {}
    return true;
  });
  const [windowKey, setWindowKey] = useState('30m');
  const [bootstrap, setBootstrap] = useState(null);
  const [decisionTree, setDecisionTree] = useState(null);
  const [symbolData, setSymbolData] = useState(null);
  const [candidates, setCandidates] = useState({ rows: [], total: 0, page: 1, page_size: 50 });
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [loading, setLoading] = useState({ bootstrap: true, dashboard: true, candidates: true, action: false });
  const [error, setError] = useState({ bootstrap: null, dashboard: null, candidates: null, action: null });
  const [actionResult, setActionResult] = useState(null);
  const [confirmState, setConfirmState] = useState(null);
  const [signalEnabled, setSignalEnabled] = useState(true);
  const [premiumForm, setPremiumForm] = useState({ user_id: '', action: 'add', days: '30' });
  const [creditsForm, setCreditsForm] = useState({ user_id: '', amount: '100' });
  const [broadcastForm, setBroadcastForm] = useState({ audience: 'all', message: '' });

  useEffect(() => {
    try {
      localStorage.setItem(ADMIN_THEME_STORAGE_KEY, isDarkMode ? 'dark' : 'light');
    } catch {}
  }, [isDarkMode]);

  const loadBootstrap = async () => {
    setLoading((prev) => ({ ...prev, bootstrap: true }));
    setError((prev) => ({ ...prev, bootstrap: null }));
    try {
      const resp = await apiFetch('/dashboard/admin/bootstrap');
      if (!resp.ok) throw new Error(await readError(resp, 'Failed to load admin bootstrap'));
      const data = await resp.json();
      setBootstrap(data);
      setSignalEnabled(Boolean(data?.summary_cards?.signals?.enabled));
    } catch (err) {
      setError((prev) => ({ ...prev, bootstrap: err.message || 'Failed to load bootstrap' }));
    } finally {
      setLoading((prev) => ({ ...prev, bootstrap: false }));
    }
  };

  const loadDecisionTree = async (nextWindow = windowKey) => {
    setLoading((prev) => ({ ...prev, dashboard: true }));
    setError((prev) => ({ ...prev, dashboard: null }));
    try {
      const [summaryResp, symbolsResp] = await Promise.all([
        apiFetch(`/dashboard/admin/decision-tree?window=${encodeURIComponent(nextWindow)}`),
        apiFetch(`/dashboard/admin/decision-tree/symbols?window=${encodeURIComponent(nextWindow)}`),
      ]);
      if (!summaryResp.ok) throw new Error(await readError(summaryResp, 'Failed to load dashboard'));
      if (!symbolsResp.ok) throw new Error(await readError(symbolsResp, 'Failed to load symbol breakdown'));
      setDecisionTree(await summaryResp.json());
      setSymbolData(await symbolsResp.json());
    } catch (err) {
      setError((prev) => ({ ...prev, dashboard: err.message || 'Failed to load dashboard' }));
    } finally {
      setLoading((prev) => ({ ...prev, dashboard: false }));
    }
  };

  const loadCandidates = async (nextPage = page, nextPageSize = pageSize, nextFilters = filters, nextWindow = windowKey) => {
    setLoading((prev) => ({ ...prev, candidates: true }));
    setError((prev) => ({ ...prev, candidates: null }));
    const params = new URLSearchParams({
      window: nextWindow,
      page: String(nextPage),
      page_size: String(nextPageSize),
    });
    Object.entries(nextFilters).forEach(([key, value]) => {
      if (String(value || '').trim()) params.set(key, String(value).trim());
    });
    try {
      const resp = await apiFetch(`/dashboard/admin/trade-candidates?${params.toString()}`);
      if (!resp.ok) throw new Error(await readError(resp, 'Failed to load trade candidates'));
      setCandidates(await resp.json());
    } catch (err) {
      setError((prev) => ({ ...prev, candidates: err.message || 'Failed to load candidates' }));
    } finally {
      setLoading((prev) => ({ ...prev, candidates: false }));
    }
  };

  useEffect(() => {
    loadBootstrap();
  }, []);

  useEffect(() => {
    loadDecisionTree(windowKey);
    loadCandidates(1, pageSize, filters, windowKey);
    setPage(1);
  }, [windowKey]);

  const refreshAll = async () => {
    await Promise.all([loadBootstrap(), loadDecisionTree(windowKey), loadCandidates(page, pageSize, filters, windowKey)]);
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = async () => {
    setPage(1);
    await loadCandidates(1, pageSize, filters, windowKey);
  };

  const resetFilters = async () => {
    setFilters(EMPTY_FILTERS);
    setPage(1);
    await loadCandidates(1, pageSize, EMPTY_FILTERS, windowKey);
  };

  const exportCandidates = async (format = 'json') => {
    const params = new URLSearchParams({ window: windowKey, fmt: format });
    Object.entries(filters).forEach(([key, value]) => {
      if (String(value || '').trim()) params.set(key, String(value).trim());
    });
    const resp = await apiFetch(`/dashboard/admin/trade-candidates/export?${params.toString()}`);
    if (!resp.ok) throw new Error(await readError(resp, 'Failed to export candidates'));
    const blob = await resp.blob();
    const disposition = resp.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename=\"([^\"]+)\"/);
    const filename = match?.[1] || `trade_candidates.${format === 'csv' ? 'csv' : 'json'}`;
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  };

  const runAction = async (endpoint, payload, successPrefix) => {
    setLoading((prev) => ({ ...prev, action: true }));
    setError((prev) => ({ ...prev, action: null }));
    try {
      const resp = await apiFetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload || {}),
      });
      if (!resp.ok) throw new Error(await readError(resp, 'Action failed'));
      const data = await resp.json();
      setActionResult(`${successPrefix}: ${data.message || 'Success'}`);
      await loadBootstrap();
      if (endpoint.includes('signal-control')) {
        setSignalEnabled(Boolean(data?.signal?.enabled));
      }
      return true;
    } catch (err) {
      setError((prev) => ({ ...prev, action: err.message || 'Action failed' }));
      return false;
    } finally {
      setLoading((prev) => ({ ...prev, action: false }));
    }
  };

  const totalPages = useMemo(() => {
    const total = Number(candidates?.total || 0);
    return Math.max(1, Math.ceil(total / Math.max(Number(pageSize) || 1, 1)));
  }, [candidates, pageSize]);

  const db = decisionTree?.db || {};
  const journalMetrics = decisionTree?.journal?.metrics || {};
  const topPairs = decisionTree?.top_pairs?.pairs || [];
  const selectorHealth = decisionTree?.top_pairs?.health || {};
  const symbolEntries = Object.entries(symbolData?.symbols || {});
  const themeVars = useMemo(
    () => ({
      '--page-bg': isDarkMode ? '#070a0b' : '#f4efe6',
      '--selection-bg': isDarkMode ? 'rgba(199,165,107,0.30)' : 'rgba(179,130,57,0.24)',
      '--hero-bg': isDarkMode
        ? 'linear-gradient(135deg,#18130f 0%,#0d1011 48%,#081013 100%)'
        : 'linear-gradient(135deg,#fffaf1 0%,#f7f0e1 48%,#eef5f6 100%)',
      '--hero-border': isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(71,85,105,0.12)',
      '--panel-bg': isDarkMode ? 'rgba(16,20,21,0.82)' : 'rgba(255,251,245,0.88)',
      '--panel-bg-strong': isDarkMode ? '#0f1313' : '#fffaf2',
      '--panel-border': isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(71,85,105,0.14)',
      '--soft-border': isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(71,85,105,0.12)',
      '--card-bg': isDarkMode ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.76)',
      '--panel-shadow': isDarkMode ? '0 20px 70px rgba(0,0,0,0.35)' : '0 18px 60px rgba(15,23,42,0.12)',
      '--panel-gloss': isDarkMode
        ? 'linear-gradient(135deg,rgba(255,255,255,0.06),transparent 42%,transparent 70%,rgba(255,255,255,0.03))'
        : 'linear-gradient(135deg,rgba(255,255,255,0.92),transparent 40%,transparent 70%,rgba(199,165,107,0.08))',
      '--text-main': isDarkMode ? '#f5f5f4' : '#18212b',
      '--text-soft': isDarkMode ? '#e7e5e4' : '#24303c',
      '--text-muted': isDarkMode ? '#a8a29e' : '#52606d',
      '--text-dim': isDarkMode ? '#78716c' : '#6b7280',
      '--accent-text': '#c7a56b',
      '--accent-border': isDarkMode ? 'rgba(199,165,107,0.30)' : 'rgba(179,130,57,0.32)',
      '--accent-soft-bg': isDarkMode ? 'rgba(199,165,107,0.15)' : 'rgba(199,165,107,0.16)',
      '--accent-soft-text': isDarkMode ? '#f2ddb0' : '#8a642a',
      '--badge-neutral-bg': isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.78)',
      '--button-muted-bg': isDarkMode ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.75)',
      '--button-muted-hover': isDarkMode ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.95)',
      '--input-bg': isDarkMode ? 'rgba(0,0,0,0.20)' : 'rgba(255,255,255,0.82)',
      '--input-border': isDarkMode ? 'rgba(255,255,255,0.10)' : 'rgba(148,163,184,0.28)',
      '--surface-strong': isDarkMode ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.68)',
      '--surface-soft': isDarkMode ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.52)',
      '--line-faint': isDarkMode ? 'rgba(255,255,255,0.08)' : 'rgba(148,163,184,0.20)',
    }),
    [isDarkMode]
  );

  return (
    <div className="min-h-screen bg-[var(--page-bg)] text-[var(--text-main)]" style={themeVars}>
      <div className={`pointer-events-none fixed inset-0 ${isDarkMode ? 'bg-[radial-gradient(circle_at_top_left,rgba(199,165,107,0.16),transparent_34%),radial-gradient(circle_at_top_right,rgba(83,162,172,0.14),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent_18%)]' : 'bg-[radial-gradient(circle_at_top_left,rgba(199,165,107,0.14),transparent_34%),radial-gradient(circle_at_top_right,rgba(83,162,172,0.12),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.55),transparent_22%)]'}`} />
      <div className="relative z-10 mx-auto max-w-[1600px] px-4 py-6 md:px-8 md:py-10">
        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-[2.4rem] border border-[color:var(--hero-border)] bg-[var(--hero-bg)] p-6 md:p-8 shadow-[var(--panel-shadow)]">
            <div className="flex flex-wrap items-start justify-between gap-5">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--accent-border)] bg-[var(--accent-soft-bg)] px-3 py-1 text-[11px] font-black uppercase tracking-[0.35em] text-[var(--accent-soft-text)]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Web Admin
                </div>
                <h1 className="mt-5 max-w-3xl text-4xl font-black tracking-tight text-[var(--text-main)] md:text-5xl">
                  Decision routing, candidate quality, and operational controls now live on the web.
                </h1>
                <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--text-muted)] md:text-base">
                  This panel is the canonical admin surface. Telegram stays as the gatekeeper and redirect layer, while the live control plane and Decision Tree telemetry sit here.
                </p>
              </div>
              <div className="min-w-[240px] rounded-[1.8rem] border border-[color:var(--soft-border)] bg-[var(--card-bg)] p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--text-dim)]">Signed In</p>
                    <p className="mt-2 text-xl font-black text-[var(--text-main)]">{user?.first_name || 'Admin'}</p>
                    <p className="text-sm text-[var(--text-muted)]">@{user?.username || 'unknown'}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsDarkMode((prev) => !prev)}
                    className="inline-flex items-center gap-2 rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-3 py-2 text-xs font-bold text-[var(--text-soft)] hover:bg-[var(--button-muted-hover)]"
                  >
                    {isDarkMode ? <MoonStar className="h-3.5 w-3.5" /> : <SunMedium className="h-3.5 w-3.5" />}
                    {isDarkMode ? 'Dark on' : 'Dark off'}
                  </button>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge tone="amber">Admin JWT active</Badge>
                  <Badge tone="cyan">{humanWindow(windowKey)} live window</Badge>
                </div>
                <div className="mt-4 flex gap-2">
                  <a href="/" className="inline-flex items-center gap-2 rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-4 py-2 text-xs font-bold text-[var(--text-soft)] hover:bg-[var(--button-muted-hover)]">
                    User Dashboard
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                  <button onClick={onLogout} className="rounded-full border border-rose-400/25 bg-rose-500/10 px-4 py-2 text-xs font-bold text-rose-200 hover:bg-rose-500/20">
                    Disconnect
                  </button>
                </div>
              </div>
            </div>
            {(error.bootstrap || error.dashboard || error.candidates || error.action || actionResult) && (
              <div className="mt-6 flex flex-col gap-3">
                {[error.bootstrap, error.dashboard, error.candidates, error.action].filter(Boolean).map((msg, idx) => (
                  <div key={`${msg}-${idx}`} className="rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      <span>{msg}</span>
                    </div>
                  </div>
                ))}
                {actionResult ? (
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                    {actionResult}
                  </div>
                ) : null}
              </div>
            )}
          </section>

          <section className="rounded-[2.4rem] border border-[color:var(--panel-border)] bg-[var(--panel-bg)] p-6 shadow-[var(--panel-shadow)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-[0.35em] text-[var(--accent-text)]">Overview</p>
                <h2 className="mt-3 text-2xl font-black text-[var(--text-main)]">Admin heartbeat</h2>
              </div>
              <button onClick={refreshAll} className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-xs font-bold text-cyan-100 hover:bg-cyan-500/20">
                <RefreshCw className={`h-3.5 w-3.5 ${(loading.bootstrap || loading.dashboard || loading.candidates) ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <OverviewCard
                label="Users"
                value={fmtNumber(bootstrap?.summary_cards?.users?.total_users)}
                accent="text-white"
                note={`${fmtNumber(bootstrap?.summary_cards?.users?.premium_users)} premium / ${fmtNumber(bootstrap?.summary_cards?.users?.lifetime_users)} lifetime`}
              />
              <OverviewCard
                label="Signal Control"
                value={bootstrap?.summary_cards?.signals?.enabled ? 'ON' : 'OFF'}
                accent={bootstrap?.summary_cards?.signals?.enabled ? 'text-emerald-300' : 'text-rose-300'}
                note={`${bootstrap?.summary_cards?.signals?.timeframe || '-'} | top ${bootstrap?.summary_cards?.signals?.top_n || '-'}`}
              />
              <OverviewCard
                label="Candidate Rows"
                value={fmtNumber(bootstrap?.summary_cards?.candidates?.live_candidate_count)}
                accent="text-[#f2ddb0]"
                note={`${fmtNumber(bootstrap?.summary_cards?.candidates?.rejected_count)} rejected live rows`}
              />
              <OverviewCard
                label="Approved"
                value={fmtNumber(bootstrap?.summary_cards?.candidates?.approved_count)}
                accent="text-cyan-200"
                note="Current live-window approvals"
              />
            </div>
          </section>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <SectionShell
            eyebrow="Decision Tree"
            title="Live routing dashboard"
            action={(
              <div className="flex flex-wrap gap-2">
                {WINDOW_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setWindowKey(option.value)}
                    className={`rounded-full border px-4 py-2 text-xs font-bold transition ${
                      windowKey === option.value
                        ? 'border-[#c7a56b]/40 bg-[#c7a56b]/15 text-[#f2ddb0]'
                        : 'border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] text-[var(--text-muted)] hover:bg-[var(--button-muted-hover)]'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
          >
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <div className="flex items-center gap-2 text-[var(--text-main)]">
                  <Radio className="h-4 w-4 text-cyan-300" />
                  <p className="text-sm font-black">Top-volume universe</p>
                </div>
                <p className="mt-3 text-sm leading-7 text-[var(--text-muted)]">
                  {topPairs.length ? topPairs.join(', ') : 'No universe snapshot available yet.'}
                </p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge tone="cyan">source {selectorHealth?.source || '-'}</Badge>
                  <Badge tone="neutral">count {fmtNumber(selectorHealth?.pair_count || topPairs.length)}</Badge>
                </div>
              </div>
              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <div className="flex items-center gap-2 text-[var(--text-main)]">
                  <BarChart3 className="h-4 w-4 text-[#f2ddb0]" />
                  <p className="text-sm font-black">Live funnel</p>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <OverviewCard label="Signals" value={fmtNumber(journalMetrics.signal_generated)} accent="text-[var(--text-main)]" />
                  <OverviewCard label="V2 Apply" value={fmtNumber(journalMetrics.decision_tree_live_apply)} accent="text-cyan-200" />
                  <OverviewCard label="Rejected" value={fmtNumber(journalMetrics.v2_rejected)} accent="text-rose-200" />
                  <OverviewCard label="Cooldown" value={fmtNumber(journalMetrics.v2_rejection_cooldown_active)} accent="text-amber-100" />
                </div>
              </div>
            </div>

            <div className="mt-4 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <p className="text-sm font-black text-[var(--text-main)]">Candidate mix</p>
                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex items-center justify-between text-[var(--text-muted)]">
                    <span>Live rows</span>
                    <span className="font-bold text-[var(--text-main)]">{fmtNumber(db.live_candidate_count)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[var(--text-muted)]">
                    <span>Approved</span>
                    <span className="font-bold text-emerald-200">{fmtNumber(db.approved_count)}</span>
                  </div>
                  <div className="flex items-center justify-between text-[var(--text-muted)]">
                    <span>Rejected</span>
                    <span className="font-bold text-rose-200">{fmtNumber(db.rejected_count)}</span>
                  </div>
                </div>
                <div className="mt-5">
                  <p className="text-[11px] uppercase tracking-[0.25em] text-[var(--text-dim)]">Top rejection reasons</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(db.reject_histogram || {}).slice(0, 6).map(([label, count]) => (
                      <Badge key={label} tone="rose">{label}:{count}</Badge>
                    ))}
                  </div>
                </div>
              </div>
              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <p className="text-sm font-black text-[var(--text-main)]">Recent runtime lines</p>
                <div className="mt-4 space-y-2">
                  {(decisionTree?.journal?.recent_lines || []).slice(-5).map((line, idx) => (
                    <div key={`${line}-${idx}`} className="rounded-xl border border-[color:var(--line-faint)] bg-[var(--surface-soft)] px-3 py-2 font-mono text-[11px] text-[var(--text-muted)]">
                      {line}
                    </div>
                  ))}
                  {!decisionTree?.journal?.recent_lines?.length ? (
                    <div className="rounded-xl border border-[color:var(--line-faint)] bg-[var(--surface-soft)] px-3 py-2 text-sm text-[var(--text-dim)]">
                      No recent runtime lines for this window.
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </SectionShell>

          <SectionShell eyebrow="Symbols" title="Per-symbol funnel breakdown">
            <div className="overflow-x-auto rounded-[1.6rem] border border-[color:var(--line-faint)]">
              <div className="min-w-[820px]">
                <div className="grid grid-cols-[minmax(170px,1.5fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)] gap-2 bg-[var(--surface-soft)] px-4 py-3 text-[11px] font-black uppercase tracking-[0.2em] text-[var(--text-dim)]">
                  <span>Symbol</span>
                  <span>Scanned</span>
                  <span>Signals</span>
                  <span>Funnel</span>
                  <span>Selected</span>
                  <span>Rejected</span>
                  <span>Cooldown</span>
                </div>
                <div className="divide-y" style={{ borderColor: 'var(--line-faint)' }}>
                  {symbolEntries.slice(0, 12).map(([symbol, stats]) => (
                    <div key={symbol} className="grid grid-cols-[minmax(170px,1.5fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)_minmax(90px,0.7fr)] gap-2 px-4 py-3 text-sm text-[var(--text-soft)]">
                      <span className="font-bold text-[var(--text-main)]">{symbol}</span>
                      <span>{fmtNumber(stats.scanned)}</span>
                      <span>{fmtNumber(stats.signal_generated)}</span>
                      <span>{fmtNumber(stats.candidate_funnel)}</span>
                      <span className="text-cyan-100">{fmtNumber(stats.v2_selected)}</span>
                      <span className="text-rose-200">{fmtNumber(stats.v2_rejected)}</span>
                      <span className="text-amber-100">{fmtNumber(stats.cooldown_active)}</span>
                    </div>
                  ))}
                  {!symbolEntries.length ? (
                    <div className="px-4 py-6 text-sm text-[var(--text-dim)]">No symbol breakdown data yet for this window.</div>
                  ) : null}
                </div>
              </div>
            </div>
          </SectionShell>
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <SectionShell
            eyebrow="Trade Candidates"
            title="Searchable candidate explorer"
            action={(
              <div className="flex gap-2">
                <button onClick={() => exportCandidates('json')} className="inline-flex items-center gap-2 rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-4 py-2 text-xs font-bold text-[var(--text-soft)] hover:bg-[var(--button-muted-hover)]">
                  <Download className="h-3.5 w-3.5" />
                  JSON
                </button>
                <button onClick={() => exportCandidates('csv')} className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-xs font-bold text-cyan-100 hover:bg-cyan-500/20">
                  <Download className="h-3.5 w-3.5" />
                  CSV
                </button>
              </div>
            )}
          >
            <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
              {[
                ['symbol', 'Symbol'],
                ['engine', 'Engine'],
                ['tier', 'Tier'],
                ['regime', 'Regime'],
                ['reject_reason', 'Reject reason'],
                ['status', 'approved/rejected'],
              ].map(([key, placeholder]) => (
                <input
                  key={key}
                  value={filters[key]}
                  onChange={(e) => handleFilterChange(key, e.target.value)}
                  placeholder={placeholder}
                  className="rounded-2xl border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-main)] outline-none transition placeholder:text-[var(--text-dim)] focus:border-[color:var(--accent-border)]"
                />
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <button onClick={applyFilters} className="rounded-full border border-[#c7a56b]/30 bg-[#c7a56b]/15 px-4 py-2 text-xs font-bold text-[#f2ddb0] hover:bg-[#c7a56b]/25">
                Apply filters
              </button>
              <button onClick={resetFilters} className="rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-4 py-2 text-xs font-bold text-[var(--text-soft)] hover:bg-[var(--button-muted-hover)]">
                Reset
              </button>
              <div className="ml-auto flex flex-wrap items-center gap-2 text-xs text-[var(--text-muted)]">
                <span>Page size</span>
                <ChipSelector
                  options={PAGE_SIZE_OPTIONS.map((size) => ({ value: size, label: String(size) }))}
                  value={pageSize}
                  tone="cyan"
                  compact
                  onChange={async (nextSize) => {
                    setPageSize(Number(nextSize));
                    setPage(1);
                    await loadCandidates(1, Number(nextSize), filters, windowKey);
                  }}
                />
              </div>
            </div>

            <div className="mt-5 overflow-hidden rounded-[1.6rem] border border-[color:var(--line-faint)]">
              <div className="grid grid-cols-[1.2fr_0.6fr_0.7fr_0.7fr_1fr_0.7fr_0.7fr] gap-2 bg-[var(--card-bg)] px-4 py-3 text-[11px] font-black uppercase tracking-[0.18em] text-[var(--text-dim)]">
                <span>Candidate</span>
                <span>Status</span>
                <span>Tier</span>
                <span>Engine</span>
                <span>Reject</span>
                <span>Tradeability</span>
                <span>Final</span>
              </div>
              <div className="divide-y" style={{ borderColor: 'var(--line-faint)' }}>
                {(candidates.rows || []).map((row) => (
                  <div key={`${row.id}-${row.created_at}`} className="grid grid-cols-[1.2fr_0.6fr_0.7fr_0.7fr_1fr_0.7fr_0.7fr] gap-2 px-4 py-3 text-sm">
                    <div>
                      <p className="font-bold text-[var(--text-main)]">{row.symbol} {row.side}</p>
                      <p className="text-xs text-[var(--text-dim)]">{row.regime || '-'} · {row.setup_name || '-'}</p>
                    </div>
                    <div>{row.approved ? <Badge tone="green">approved</Badge> : <Badge tone="rose">rejected</Badge>}</div>
                    <div className="text-[var(--text-soft)]">{row.user_equity_tier || '-'}</div>
                    <div className="text-[var(--text-soft)]">{row.engine || '-'}</div>
                    <div className="truncate text-[var(--text-muted)]">{row.reject_reason || row.display_reason || '-'}</div>
                    <div className="text-[var(--text-soft)]">{fmtScore(row.tradeability_score)}</div>
                    <div className="text-[#f2ddb0]">{fmtScore(row.final_score)}</div>
                  </div>
                ))}
                {!(candidates.rows || []).length ? (
                  <div className="px-4 py-6 text-sm text-[var(--text-muted)]">No candidate rows matched the current filters.</div>
                ) : null}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between gap-4 text-sm text-[var(--text-muted)]">
              <div>
                Showing {fmtNumber((candidates.rows || []).length)} of {fmtNumber(candidates.total)} rows
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={async () => {
                    const next = Math.max(page - 1, 1);
                    setPage(next);
                    await loadCandidates(next, pageSize, filters, windowKey);
                  }}
                  disabled={page <= 1}
                  className="rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-4 py-2 text-xs font-bold text-[var(--text-soft)] disabled:opacity-40"
                >
                  Prev
                </button>
                <span className="text-xs uppercase tracking-[0.2em] text-[var(--text-dim)]">Page {page} / {totalPages}</span>
                <button
                  onClick={async () => {
                    const next = Math.min(page + 1, totalPages);
                    setPage(next);
                    await loadCandidates(next, pageSize, filters, windowKey);
                  }}
                  disabled={page >= totalPages}
                  className="rounded-full border border-[color:var(--soft-border)] bg-[var(--button-muted-bg)] px-4 py-2 text-xs font-bold text-[var(--text-soft)] disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </SectionShell>

          <SectionShell eyebrow="Controls" title="Admin actions and runtime switches">
            <div className="grid gap-4">
              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-[var(--text-main)]">Signal control</p>
                    <p className="mt-1 text-xs text-[var(--text-muted)]">Toggles the shared autosignal state used by the runtime scanner.</p>
                  </div>
                  <Badge tone={signalEnabled ? 'green' : 'rose'}>{signalEnabled ? 'ON' : 'OFF'}</Badge>
                </div>
                <div className="mt-4 flex gap-3">
                  <button
                    onClick={() => setConfirmState({
                      title: `Turn AutoSignal ${signalEnabled ? 'off' : 'on'}?`,
                      description: 'This updates the shared autosignal state that the runtime scanner reads from disk-backed state.',
                      confirmLabel: signalEnabled ? 'Disable' : 'Enable',
                      tone: signalEnabled ? 'rose' : 'cyan',
                      action: () => runAction('/dashboard/admin/signal-control', { enabled: !signalEnabled }, 'Signal control updated'),
                    })}
                    className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-xs font-bold text-cyan-100 hover:bg-cyan-500/20"
                  >
                    {signalEnabled ? 'Disable' : 'Enable'}
                  </button>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <p className="text-sm font-black text-[var(--text-main)]">Premium and lifetime</p>
                <div className="mt-4 flex flex-wrap gap-2 rounded-[1.4rem] border border-[color:var(--soft-border)] bg-[var(--card-bg)] p-2">
                  {PREMIUM_ACTION_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setPremiumForm((prev) => ({ ...prev, action: option.value }))}
                      className={`rounded-full px-4 py-2 text-xs font-bold transition ${
                        premiumForm.action === option.value
                          ? option.value === 'remove'
                            ? 'border border-rose-400/25 bg-rose-500/15 text-rose-100'
                            : 'border border-[#c7a56b]/30 bg-[#c7a56b]/15 text-[#f2ddb0]'
                          : 'border border-[color:var(--soft-border)] bg-[var(--input-bg)] text-[var(--text-muted)] hover:bg-[var(--button-muted-hover)]'
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
                <div className="mt-3 grid gap-3 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.95fr)_auto]">
                  <input value={premiumForm.user_id} onChange={(e) => setPremiumForm((prev) => ({ ...prev, user_id: e.target.value }))} placeholder="Telegram ID" className="min-w-0 rounded-2xl border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-main)] outline-none placeholder:text-[var(--text-dim)]" />
                  {premiumForm.action === 'add' ? (
                    <input value={premiumForm.days} onChange={(e) => setPremiumForm((prev) => ({ ...prev, days: e.target.value }))} placeholder="Days" className="min-w-0 rounded-2xl border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-main)] outline-none placeholder:text-[var(--text-dim)]" />
                  ) : (
                    <div className="flex min-w-0 items-center rounded-2xl border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-muted)]">
                      {premiumForm.action === 'lifetime' ? 'Permanent premium access will be granted.' : 'Premium access will be removed immediately.'}
                    </div>
                  )}
                  <button
                    onClick={() => setConfirmState({
                      title: 'Apply premium update?',
                      description: `User ${premiumForm.user_id || '-'} will receive the premium action '${premiumForm.action}'.`,
                      confirmLabel: 'Apply',
                      tone: 'amber',
                      action: () => runAction(
                        '/dashboard/admin/premium',
                        {
                          user_id: Number(premiumForm.user_id),
                          action: premiumForm.action,
                          days: premiumForm.action === 'add' ? Number(premiumForm.days || 30) : undefined,
                        },
                        'Premium updated',
                      ),
                    })}
                    className="w-full xl:w-auto rounded-full border border-[#c7a56b]/30 bg-[#c7a56b]/15 px-4 py-3 text-xs font-bold text-[#f2ddb0] hover:bg-[#c7a56b]/25"
                  >
                    Apply
                  </button>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <p className="text-sm font-black text-[var(--text-main)]">Credits</p>
                <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
                  <input value={creditsForm.user_id} onChange={(e) => setCreditsForm((prev) => ({ ...prev, user_id: e.target.value }))} placeholder="Telegram ID" className="min-w-0 rounded-2xl border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-main)] outline-none placeholder:text-[var(--text-dim)]" />
                  <input value={creditsForm.amount} onChange={(e) => setCreditsForm((prev) => ({ ...prev, amount: e.target.value }))} placeholder="Amount" className="min-w-0 rounded-2xl border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-main)] outline-none placeholder:text-[var(--text-dim)]" />
                  <button
                    onClick={() => setConfirmState({
                      title: 'Grant credits?',
                      description: `User ${creditsForm.user_id || '-'} will receive ${creditsForm.amount || 0} credits.`,
                      confirmLabel: 'Grant',
                      tone: 'cyan',
                      action: () => runAction(
                        '/dashboard/admin/credits',
                        { user_id: Number(creditsForm.user_id), amount: Number(creditsForm.amount) },
                        'Credits updated',
                      ),
                    })}
                    className="w-full lg:w-auto rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-3 text-xs font-bold text-cyan-100 hover:bg-cyan-500/20"
                  >
                    Grant
                  </button>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <p className="text-sm font-black text-[var(--text-main)]">Broadcast</p>
                <div className="mt-4 grid gap-3">
                  <ChipSelector
                    options={BROADCAST_AUDIENCE_OPTIONS}
                    value={broadcastForm.audience}
                    tone="amber"
                    onChange={(nextAudience) => setBroadcastForm((prev) => ({ ...prev, audience: nextAudience }))}
                  />
                  <textarea value={broadcastForm.message} onChange={(e) => setBroadcastForm((prev) => ({ ...prev, message: e.target.value }))} rows={5} placeholder="Telegram HTML message" className="rounded-[1.4rem] border border-[color:var(--input-border)] bg-[var(--input-bg)] px-4 py-3 text-sm text-[var(--text-main)] outline-none placeholder:text-[var(--text-dim)]" />
                  <div className="flex justify-end">
                    <button
                      onClick={() => setConfirmState({
                        title: 'Send broadcast?',
                        description: `This will send a Telegram broadcast to the '${broadcastForm.audience}' audience.`,
                        confirmLabel: 'Send broadcast',
                        tone: 'amber',
                        action: () => runAction(
                          '/dashboard/admin/broadcast',
                          broadcastForm,
                          'Broadcast finished',
                        ),
                      })}
                      className="inline-flex w-full sm:w-auto justify-center items-center gap-2 rounded-full border border-[#c7a56b]/30 bg-[#c7a56b]/15 px-4 py-3 text-xs font-bold text-[#f2ddb0] hover:bg-[#c7a56b]/25"
                    >
                      <Send className="h-3.5 w-3.5" />
                      Broadcast
                    </button>
                  </div>
                </div>
              </div>

              <div className="rounded-[1.6rem] border border-[color:var(--line-faint)] bg-[var(--surface-strong)] p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-black text-[var(--text-main)]">Daily report</p>
                    <p className="mt-1 text-xs text-[var(--text-muted)]">Triggers the admin daily report immediately through the same report module used by the bot runtime.</p>
                  </div>
                  <button
                    onClick={() => setConfirmState({
                      title: 'Send daily report now?',
                      description: 'This immediately sends the daily admin report to the configured admin targets.',
                      confirmLabel: 'Send report',
                      tone: 'cyan',
                      action: () => runAction('/dashboard/admin/daily-report-now', {}, 'Daily report sent'),
                    })}
                    className="w-full sm:w-auto rounded-full border border-cyan-400/20 bg-cyan-500/10 px-4 py-2 text-xs font-bold text-cyan-100 hover:bg-cyan-500/20"
                  >
                    Send now
                  </button>
                </div>
              </div>
            </div>
          </SectionShell>
        </div>

        <div className="mt-6 text-center text-[10px] font-mono uppercase tracking-[0.25em] text-[var(--text-dim)]">
          Canonical admin surface · Telegram redirect layer preserved for rollback
        </div>
      </div>

      {confirmState ? (
        <ConfirmModal
          title={confirmState.title}
          description={confirmState.description}
          confirmLabel={confirmState.confirmLabel}
          tone={confirmState.tone}
          busy={loading.action}
          onCancel={() => setConfirmState(null)}
          onConfirm={async () => {
            const ok = await confirmState.action();
            if (ok) setConfirmState(null);
          }}
        />
      ) : null}
    </div>
  );
}
