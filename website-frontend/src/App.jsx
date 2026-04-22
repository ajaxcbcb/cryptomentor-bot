import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart, Wallet, Bot, Settings, LogOut,
  TrendingUp, TrendingDown, Activity, CheckCircle2,
  Shield, BarChart2, BarChart3, Target, Zap, Layers, RefreshCw,
  GraduationCap, Radio, Cpu, ToggleRight, ToggleLeft,
  Menu, X, Crosshair, ArrowUpRight, ArrowDownRight,
  PlayCircle, BookOpen, Lock, Clock, Power, StopCircle, XCircle,
  Users, Copy, CheckCheck, ExternalLink, AlertCircle
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import bitunixLogo from './assets/bitunix.jpg';
import AdminPanel, { AdminDeniedScreen } from './AdminPanel';

const _CONFIGURED_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const _FALLBACK_BASE = '/api';
const FALLBACK_REFERRAL_URL = 'https://www.bitunix.com/register?vipCode=sq45';
const BUILD_MARKER = (typeof __APP_BUILD_MARKER__ !== 'undefined' && __APP_BUILD_MARKER__) || import.meta.env.VITE_BUILD_MARKER || 'dev-local';
const MIXED_AUTO_LOCK_REASON = 'Mixed mode uses per-symbol auto routing and bypasses legacy global auto-switch.';

// Tracks which base URL is confirmed working so we don't retry every call.
// null = untested, string = confirmed working base.
let _resolvedBase = null;
let _runtimeToken = null;
const _isServerError = (status) => Number(status) >= 500;

const apiFetch = async (path, opts = {}) => {
  let token = null;
  try { token = localStorage.getItem('cm_token'); } catch {}
  if (!token && _runtimeToken) token = _runtimeToken;
  const headers = {
    ...(opts.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  // If we already confirmed a working base, use it directly.
  if (_resolvedBase) {
    let r = await fetch(`${_resolvedBase}${path}`, { ...opts, headers });
    // If configured base starts returning 5xx, fail over to same-origin /api.
    if (
      _resolvedBase === _CONFIGURED_BASE &&
      _CONFIGURED_BASE !== _FALLBACK_BASE &&
      _isServerError(r.status)
    ) {
      console.warn(`[apiFetch] ${_CONFIGURED_BASE} returned ${r.status}, retrying via ${_FALLBACK_BASE}`);
      try {
        const fallbackResp = await fetch(`${_FALLBACK_BASE}${path}`, { ...opts, headers });
        if (!_isServerError(fallbackResp.status)) {
          _resolvedBase = _FALLBACK_BASE;
        }
        r = fallbackResp;
      } catch (_fallbackErr) {
        // Keep original response from configured base.
      }
    }
    if (r.status === 403) window.dispatchEvent(new CustomEvent('cm:verification_required'));
    return r;
  }

  // Try the configured base first.
  try {
    const r = await fetch(`${_CONFIGURED_BASE}${path}`, { ...opts, headers });
    if (!_isServerError(r.status)) {
      _resolvedBase = _CONFIGURED_BASE; // mark as working only when not 5xx
    } else if (_CONFIGURED_BASE !== _FALLBACK_BASE) {
      console.warn(`[apiFetch] ${_CONFIGURED_BASE} returned ${r.status}, falling back to ${_FALLBACK_BASE}`);
      try {
        const fallbackResp = await fetch(`${_FALLBACK_BASE}${path}`, { ...opts, headers });
        if (!_isServerError(fallbackResp.status)) {
          _resolvedBase = _FALLBACK_BASE;
        }
        if (fallbackResp.status === 403) window.dispatchEvent(new CustomEvent('cm:verification_required'));
        return fallbackResp;
      } catch (_fallbackErr) {
        // Return original 5xx response from configured base.
      }
    }
    if (r.status === 401) console.warn('[apiFetch] 401 on:', path);
    if (r.status === 403) window.dispatchEvent(new CustomEvent('cm:verification_required'));
    return r;
  } catch (_networkErr) {
    // Configured base is unreachable (wrong domain, CORS block, etc.).
    // Fall back to same-origin /api which nginx proxies to the backend.
    if (_CONFIGURED_BASE !== _FALLBACK_BASE) {
      console.warn(`[apiFetch] ${_CONFIGURED_BASE} unreachable, falling back to ${_FALLBACK_BASE}`);
      try {
        const r = await fetch(`${_FALLBACK_BASE}${path}`, { ...opts, headers });
        _resolvedBase = _FALLBACK_BASE; // remember fallback works
        if (r.status === 403) window.dispatchEvent(new CustomEvent('cm:verification_required'));
        return r;
      } catch (fallbackErr) {
        throw fallbackErr;
      }
    }
    throw _networkErr;
  }
};

const readApiErrorMessage = async (resp, fallback = 'Request failed') => {
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

const INITIAL_POSITIONS = [
  { id: 1, pair: "BTC/USDT", side: "LONG", entry: "$64,230.50", current: "$65,100.00", margin: "$1,000", leverage: "10x", pnl: "+$124.50", pnlPercent: "+12.45%", isProfitable: true, tp: { tp1: { price: "$64,800", hit: true }, tp2: { price: "$65,500", hit: false }, tp3: { price: "$66,000", hit: false } } },
  { id: 2, pair: "SOL/USDT", side: "SHORT", entry: "$145.20", current: "$142.10", margin: "$500", leverage: "5x", pnl: "+$31.00", pnlPercent: "+6.20%", isProfitable: true, tp: { tp1: { price: "$143.00", hit: true }, tp2: { price: "$141.50", hit: false }, tp3: { price: "$138.00", hit: false } } },
  { id: 3, pair: "ETH/USDT", side: "LONG", entry: "$3,105.00", current: "$3,080.20", margin: "$800", leverage: "5x", pnl: "-$19.84", pnlPercent: "-2.48%", isProfitable: false, tp: { tp1: { price: "$3,150", hit: false }, tp2: { price: "$3,200", hit: false }, tp3: { price: "$3,300", hit: false } } },
];

const PERFORMANCE_METRICS = { sharpeRatio: "2.14", maxDrawdown: "-12.4%", winRate: "68.5%", totalTrades: "1,248", projected1Yr: "$24,500.00", monthlyVolatility: "4.2%" };

const HISTORICAL_DATA = [
  { date: "Jan 1", equity: 10000, sharpe: "0.00", maxDd: "0.0%", winRate: "0.0%", trades: 0, volatility: "0.0%" },
  { date: "Jan 15", equity: 10250, sharpe: "1.20", maxDd: "-1.5%", winRate: "55.0%", trades: 45, volatility: "1.8%" },
  { date: "Feb 1", equity: 10800, sharpe: "1.85", maxDd: "-2.1%", winRate: "62.5%", trades: 120, volatility: "2.4%" },
  { date: "Feb 15", equity: 10450, sharpe: "1.45", maxDd: "-5.8%", winRate: "58.2%", trades: 215, volatility: "3.5%" },
  { date: "Mar 1", equity: 11200, sharpe: "1.95", maxDd: "-5.8%", winRate: "64.1%", trades: 380, volatility: "3.2%" },
  { date: "Mar 15", equity: 11950, sharpe: "2.10", maxDd: "-6.2%", winRate: "66.8%", trades: 520, volatility: "3.8%" },
  { date: "Apr 1", equity: 11600, sharpe: "1.85", maxDd: "-8.5%", winRate: "63.5%", trades: 690, volatility: "4.5%" },
  { date: "Apr 15", equity: 12800, sharpe: "2.25", maxDd: "-8.5%", winRate: "67.2%", trades: 840, volatility: "4.1%" },
  { date: "May 1", equity: 13500, sharpe: "2.40", maxDd: "-8.5%", winRate: "69.5%", trades: 980, volatility: "3.9%" },
  { date: "May 15", equity: 13150, sharpe: "2.15", maxDd: "-11.2%", winRate: "66.4%", trades: 1120, volatility: "4.6%" },
  { date: "Jun 1", equity: 14600, sharpe: "2.35", maxDd: "-11.2%", winRate: "68.1%", trades: 1210, volatility: "4.3%" },
  { date: "Jun 15", equity: 15850, sharpe: "2.14", maxDd: "-12.4%", winRate: "68.5%", trades: 1248, volatility: "4.2%" }
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0a0a0a]/90 backdrop-blur-md border border-cyan-500/30 p-3 rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.2)]">
        <p className="text-slate-400 text-[10px] font-bold mb-1 uppercase tracking-wider">{label}</p>
        <p className="text-cyan-400 font-black text-lg flex items-center gap-1.5">
          ${payload[0].value.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};

const MOCK_SIGNALS = [
  { id: 1, pair: "BTC/USDT", type: "Scalp", direction: "LONG", entry: "64,200 - 64,500", targets: ["64,800", "65,500", "66,000"], stopLoss: "63,800", status: "Active", time: "10m ago", premium: false, confidence: 92 },
  { id: 2, pair: "ETH/USDT", type: "Swing", direction: "SHORT", entry: "3,150 - 3,200", targets: ["3,000", "2,850"], stopLoss: "3,300", status: "Waiting Zone", time: "1h ago", premium: true, confidence: 85 },
  { id: 3, pair: "AVAX/USDT", type: "Scalp", direction: "LONG", entry: "34.50 - 35.00", targets: ["36.00", "38.50"], stopLoss: "33.20", status: "Active", time: "2h ago", premium: true, confidence: 88 },
];

const MOCK_COURSES = [
  { id: 1, title: "Risk Management 101", category: "Basics", progress: 100, lessons: 5, locked: false },
  { id: 2, title: "StackMentor 3-Tier Execution", category: "Advanced", progress: 60, lessons: 8, locked: false },
  { id: 3, title: "Institutional Order Flow", category: "Masterclass", progress: 0, lessons: 12, locked: true },
];

const RISK_OPTIONS = [0.25, 0.5, 1, 2, 3, 5, 7.5, 10];
const ONE_CLICK_RISK_OPTIONS = [3, 5, 10, 25, 50, 100];
const LOW_EQUITY_THRESHOLD_USD = 30;
const LOW_EQUITY_MIN_RISK_PCT = 3;

const normalizeAutoRisk = (raw) => {
  const n = Number(raw);
  if (!Number.isFinite(n)) return 3;
  if (n <= 0.25) return 0.25;
  if (n >= 10) return 10;
  return Math.round(n * 100) / 100;
};

const getAutoRiskFloorByEquity = (equity) => {
  const eq = Number(equity);
  if (Number.isFinite(eq) && eq > 0 && eq < LOW_EQUITY_THRESHOLD_USD) {
    return LOW_EQUITY_MIN_RISK_PCT;
  }
  return 0.25;
};

const normalizeOneClickRisk = (raw) => {
  const n = Number(raw);
  if (!Number.isFinite(n)) return 3;
  let closest = ONE_CLICK_RISK_OPTIONS[0];
  let minDiff = Math.abs(n - closest);
  for (const tier of ONE_CLICK_RISK_OPTIONS) {
    const diff = Math.abs(n - tier);
    if (diff < minDiff || (diff === minDiff && tier > closest)) {
      closest = tier;
      minDiff = diff;
    }
  }
  return closest;
};

const oneClickSliderValueFromRisk = (risk) => {
  const normalized = normalizeOneClickRisk(risk);
  const idx = ONE_CLICK_RISK_OPTIONS.findIndex((tier) => tier === normalized);
  return idx >= 0 ? idx : 0;
};

const oneClickRiskFromSliderValue = (sliderValue) => {
  const idx = Number(sliderValue);
  if (!Number.isFinite(idx)) return ONE_CLICK_RISK_OPTIONS[0];
  const safeIdx = Math.max(0, Math.min(ONE_CLICK_RISK_OPTIONS.length - 1, Math.round(idx)));
  return ONE_CLICK_RISK_OPTIONS[safeIdx];
};

const makeClientRequestId = () => {
  try {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  } catch {}
  return `req_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
};

const mapOneClickReasonMessage = (detail) => {
  const fallback = typeof detail === 'string' ? detail : 'Order failed';
  if (!detail || typeof detail !== 'object') return fallback;
  const code = String(detail.reason_code || '').toLowerCase();
  const reason = String(detail.reason || detail.message || fallback);
  const map = {
    blocked_pending_order: 'Order blocked: there is already a pending order for this symbol.',
    pending_order: 'Order blocked: pending request still in progress.',
    existing_position: 'Order blocked: you already have an open managed position on this symbol.',
    existing_position_opposite_side: 'Order blocked: opposite-side position is already open.',
    exchange_position_exists: 'Order blocked: exchange shows an open position on this symbol.',
    exchange_position_opposite_side: 'Order blocked: exchange has opposite-side position open.',
    blocked_cooldown: 'Order blocked: symbol is in cooldown window after recent close.',
    client_request_id_reused_expired_window: 'Request ID already used. Retry from preview to generate a new request.',
    idempotent_replay_non_open: 'This request was already processed and did not open a position.',
    validation_error: reason || 'Sizing validation failed for this setup.',
  };
  return map[code] || reason || fallback;
};

const getRiskButtonTone = (risk) => {
  const r = Number(risk) || 0;
  if (r > 5.0) return 'bg-gradient-to-r from-amber-500/20 to-rose-500/20 text-amber-300 border border-amber-400/40';
  return 'bg-green-500/20 text-green-400 border border-green-500/30';
};

const getRiskValueTone = (risk) => {
  const r = Number(risk) || 0;
  if (r > 5.0) return 'text-amber-300';
  return 'text-green-400';
};

const getRiskDescription = (risk) => {
  const r = Number(risk) || 0;
  if (r > 5.0) return '🟠 Amber-Red Risk Zone (>5%) — high exposure and drawdown sensitivity';
  if (r === 5.0) return '🟢 Green Risk Zone (5%) — upper safe bound for AutoTrade';
  return '🟢 Green Risk Zone (<5%) — conservative exposure and smoother drawdowns';
};

const getOneClickRiskButtonTone = (risk, selected = false) => {
  const r = Number(risk) || 0;
  if (r >= 10) return selected
    ? 'bg-gradient-to-r from-yellow-500/30 to-orange-500/25 text-yellow-100 border border-yellow-400/55 shadow-[0_0_0_1px_rgba(250,204,21,0.3)]'
    : 'bg-[#111006] text-yellow-300/85 border border-yellow-500/30 hover:border-yellow-400/55 hover:text-yellow-200';
  if (r >= 5) return selected
    ? 'bg-gradient-to-r from-lime-500/30 to-yellow-500/25 text-lime-100 border border-lime-400/55 shadow-[0_0_0_1px_rgba(132,204,22,0.3)]'
    : 'bg-[#081108] text-lime-300/85 border border-lime-500/30 hover:border-lime-400/55 hover:text-lime-200';
  return selected
    ? 'bg-gradient-to-r from-green-500/35 to-emerald-500/30 text-green-100 border border-green-400/60 shadow-[0_0_0_1px_rgba(74,222,128,0.3)]'
    : 'bg-[#071109] text-green-300/85 border border-green-500/30 hover:border-green-400/55 hover:text-green-200';
};

const getOneClickRiskValueTone = (risk) => {
  const r = Number(risk) || 0;
  if (r >= 10) return 'text-yellow-300';
  if (r >= 5) return 'text-lime-300';
  return 'text-green-400';
};

const getOneClickRiskDescription = (risk) => {
  const r = Number(risk) || 0;
  if (r >= 100) return '🔴 All-In (100%) — maximum exposure, use only with strict discipline';
  if (r > 10) return '🟠 High-Risk Zone (>10%) — elevated drawdown sensitivity';
  if (r >= 10) return '🟡 Elevated Risk Zone (10%) — high volatility sensitivity';
  return '🟢 Guarded Zone (3% / 5%) — lower exposure tiers';
};

const getOneClickRiskPanelTone = (risk) => {
  const r = Number(risk) || 0;
  if (r >= 10) return 'bg-yellow-500/10 border border-yellow-500/25';
  if (r >= 5) return 'bg-lime-500/10 border border-lime-500/25';
  return 'bg-green-500/10 border border-green-500/25';
};

const sanitizeCommunityCode = (value) => String(value || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 32);

const resolveReferralUi = (referralUrl, referralSource, referralCode) => {
  const code = sanitizeCommunityCode(referralCode);
  return {
    url: referralUrl || FALLBACK_REFERRAL_URL,
    source: referralSource === 'dynamic' ? 'dynamic' : 'fallback',
    code: code || null,
  };
};

const VALID_DASHBOARD_TABS = new Set(['portfolio', 'engine', 'settings', 'signals', 'referral']);

const parseDashboardDeepLink = () => {
  if (typeof window === 'undefined') {
    return { tab: null, signal_id: null, action: null };
  }
  const params = new URLSearchParams(window.location.search);
  const rawTab = String(params.get('tab') || '').trim().toLowerCase();
  const tab = VALID_DASHBOARD_TABS.has(rawTab) ? rawTab : null;
  const signal_id = String(params.get('signal_id') || '').trim() || null;
  const action = String(params.get('action') || '').trim().toLowerCase() || null;
  return { tab, signal_id, action };
};

export default function App() {
  const UPDATE_DISMISS_KEY = 'cm_update_dismissed_marker';
  const isAdminRoute = typeof window !== 'undefined' && window.location.pathname.startsWith('/admin');
  const [deepLinkContext, setDeepLinkContext] = useState(() => parseDashboardDeepLink());
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem('cm_user');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  });
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    // Only consider logged in if BOTH cm_user AND cm_token exist
    const hasUser = !!localStorage.getItem('cm_user');
    const hasToken = !!localStorage.getItem('cm_token');
    if (hasUser && !hasToken) {
      // Stale session — clear it so user re-authenticates properly
      try { localStorage.removeItem('cm_user'); } catch {}
      return false;
    }
    return hasUser && hasToken;
  });
  const [activeTab, setActiveTab] = useState(() => parseDashboardDeepLink().tab || 'portfolio');
  const [positions] = useState(INITIAL_POSITIONS);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [realPositions, setRealPositions] = useState([]);
  const [realPnl, setRealPnl] = useState(0);
  const [cumulativePnl, setCumulativePnl] = useState(0);
  const [hasCumulativePnl, setHasCumulativePnl] = useState(false);
  const [equity, setEquity] = useState(null);
  const [connectorStatus, setConnectorStatus] = useState({ linked: null, online: null, error: null });
  const [portfolioLoaded, setPortfolioLoaded] = useState(false);
  const [engineState, setEngineState] = useState({
    autoModeEnabled: true,
    autoModeLocked: false,
    autoModeLockReason: null,
    tradingMode: 'swing',
    stackMentorActive: true,
    riskMode: 'moderate',
  });
  const [engineControlBusy, setEngineControlBusy] = useState({
    autoMode: false,
    mode: false,
    stackMentor: false,
  });
  const [engineControlError, setEngineControlError] = useState(null);
  const [botRunning, setBotRunning] = useState(false);
  const [botBusy, setBotBusy] = useState(false);
  const [botError, setBotError] = useState(null);
  const [showBotStartModal, setShowBotStartModal] = useState(false);
  const [verStatus, setVerStatus] = useState(null); // null = loading, object = loaded
  const [refCode, setRefCode] = useState(() => {
    try {
      return String(localStorage.getItem('cm_ref') || '').trim().toLowerCase();
    } catch {
      return '';
    }
  });
  const [referralContext, setReferralContext] = useState({
    bitunix_referral_url: FALLBACK_REFERRAL_URL,
    ref_source: 'fallback',
    community_code: null,
  });
  const [riskSettings, setRiskSettings] = useState({
    risk_per_trade: 3,
    leverage: 10,
    leverage_baseline: 10,
    leverage_mode: 'auto_max_pair',
    leverage_note: 'AutoTrade executes with max leverage allowed for each pair.',
    leverage_range: { min: 1, max: 200 },
    margin_mode: 'cross',
    equity: 0,
    balance: 0,
    frozen: 0,
    unrealized_pnl: 0,
    loading: true,
    error: null,
  });
  const [oneClickRiskPct, setOneClickRiskPct] = useState(3);
  const [verLoading, setVerLoading] = useState(true);
  const [bootIssue, setBootIssue] = useState(null);
  const [updateNotice, setUpdateNotice] = useState({ visible: false, latest: null });
  const [userProfileHydrated, setUserProfileHydrated] = useState(false);
  const audioCtxRef = useRef(null);
  const audioUnlockedRef = useRef(false);
  const prevPositionIdsRef = useRef(new Set());
  const positionsBaselineSetRef = useRef(false);
  const referralReqSeqRef = useRef(0);

  const unlockAudio = () => {
    try {
      if (audioUnlockedRef.current) return;
      if (typeof window === 'undefined') return;
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      if (!audioCtxRef.current) audioCtxRef.current = new AC();
      if (audioCtxRef.current.state === 'suspended') {
        audioCtxRef.current.resume().catch(() => {});
      }
      audioUnlockedRef.current = true;
    } catch {}
  };

  const playTradeSound = (kind) => {
    try {
      if (!audioUnlockedRef.current) return;
      const ctx = audioCtxRef.current;
      if (!ctx) return;
      const start = ctx.currentTime + 0.01;
      const pattern = kind === 'open'
        ? [660, 880, 1046]    // upward chime
        : [740, 554, 440];    // downward close cue

      pattern.forEach((freq, i) => {
        const t = start + i * 0.12;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(0.0001, t);
        gain.gain.exponentialRampToValueAtTime(0.08, t + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.11);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + 0.12);
      });
    } catch {}
  };

  useEffect(() => {
    document.body.style.overflow = isMobileMenuOpen ? 'hidden' : 'unset';
  }, [isMobileMenuOpen]);

  useEffect(() => {
    if (!isLoggedIn) return;
    const handler = () => {
      unlockAudio();
      window.removeEventListener('pointerdown', handler);
      window.removeEventListener('keydown', handler);
      window.removeEventListener('touchstart', handler);
    };
    window.addEventListener('pointerdown', handler);
    window.addEventListener('keydown', handler);
    window.addEventListener('touchstart', handler);
    return () => {
      window.removeEventListener('pointerdown', handler);
      window.removeEventListener('keydown', handler);
      window.removeEventListener('touchstart', handler);
    };
  }, [isLoggedIn]);

  // Auto-login from Telegram Bot (Phase 1 Migration)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('t') || params.get('token');
    const urlUserStr = params.get('u') || params.get('user');
    const urlRef = params.get('ref');
    const initialDeepLink = parseDashboardDeepLink();
    setDeepLinkContext(initialDeepLink);

    // Persist referral code if present in URL
    if (urlRef) {
      const normalizedRef = String(urlRef).trim().toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 32);
      localStorage.setItem('cm_ref', normalizedRef);
      setRefCode(normalizedRef);
      console.log('[Phase1] Captured referral code:', normalizedRef);
    }

    const parseJwtPayload = (jwtToken) => {
      try {
        const parts = String(jwtToken || '').split('.');
        if (parts.length < 2) return null;
        const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        const padded = b64.padEnd(Math.ceil(b64.length / 4) * 4, '=');
        return JSON.parse(atob(padded));
      } catch {
        return null;
      }
    };

    if (urlToken) {
      try {
        _runtimeToken = urlToken;
        const payload = parseJwtPayload(urlToken) || {};
        const baseName = payload.first_name || payload.username || String(payload.sub || 'User');
        const fallbackUser = {
          id: String(payload.sub || ''),
          first_name: baseName,
          username: String(payload.username || baseName || 'user').replace(/^@/, ''),
          photo_url: `https://ui-avatars.com/api/?name=${encodeURIComponent(baseName || 'User')}&background=d946ef&color=fff&bold=true`,
          is_premium: false,
          credits: 0,
        };

        let parsedUser = null;
        if (urlUserStr) {
          try {
            parsedUser = JSON.parse(decodeURIComponent(urlUserStr));
          } catch {
            parsedUser = null;
          }
        }

        const nextUser = {
          ...fallbackUser,
          ...(parsedUser || {}),
          id: String((parsedUser && parsedUser.id) || fallbackUser.id || ''),
          username: String(((parsedUser && parsedUser.username) || fallbackUser.username || 'user')).replace(/^@/, ''),
          first_name: (parsedUser && parsedUser.first_name) || fallbackUser.first_name || 'User',
          photo_url: (parsedUser && parsedUser.photo_url) || fallbackUser.photo_url,
          is_premium: Boolean((parsedUser && parsedUser.is_premium) || false),
          credits: Number((parsedUser && parsedUser.credits) || 0),
          is_admin: Boolean((parsedUser && parsedUser.is_admin) || false),
        };

        localStorage.setItem('cm_token', urlToken);
        localStorage.setItem('cm_user', JSON.stringify(nextUser));
        setUser(nextUser);
        setIsLoggedIn(true);
        setUserProfileHydrated(Boolean((parsedUser && typeof parsedUser.is_admin !== 'undefined') || nextUser.is_admin));

        // Remove auth bootstrap params while preserving deep-link context.
        params.delete('t');
        params.delete('token');
        params.delete('u');
        params.delete('user');
        const retained = params.toString();
        window.history.replaceState(
          {},
          document.title,
          retained ? `${window.location.pathname}?${retained}` : window.location.pathname
        );
        console.log('[Phase1] Auto-login successful via bot link');
      } catch (e) {
        console.error('[Phase1] Auto-login parse error:', e);
      }
    }
  }, []);

  useEffect(() => {
    if (!isLoggedIn) return;
    if (deepLinkContext?.tab && deepLinkContext.tab !== activeTab) {
      setActiveTab(deepLinkContext.tab);
    }
  }, [isLoggedIn, deepLinkContext?.tab]);

  const handleTelegramLogin = async (telegramUser) => {
    const photoUrl = telegramUser.photo_url ||
      `https://ui-avatars.com/api/?name=${encodeURIComponent(telegramUser.first_name)}&background=d946ef&color=fff&bold=true`;

    // Call backend to verify Telegram auth and get JWT
    try {
      let resp = await fetch(`${_CONFIGURED_BASE}/auth/telegram`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(telegramUser),
      });
      if (_isServerError(resp.status) && _CONFIGURED_BASE !== _FALLBACK_BASE) {
        console.warn(`[Auth] ${_CONFIGURED_BASE} returned ${resp.status}, retrying via ${_FALLBACK_BASE}`);
        try {
          const fallbackResp = await fetch(`${_FALLBACK_BASE}/auth/telegram`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(telegramUser),
          });
          if (!_isServerError(fallbackResp.status)) {
            _resolvedBase = _FALLBACK_BASE;
          }
          resp = fallbackResp;
        } catch (_fallbackErr) {
          // Keep original 5xx response and show it to user.
        }
      }
      if (resp.ok) {
        const data = await resp.json();
        if (data.access_token) {
          _runtimeToken = data.access_token;
          localStorage.setItem('cm_token', data.access_token);
          console.log('[Auth] JWT token saved, length:', data.access_token.length);
        } else {
          console.warn('[Auth] No access_token in response:', data);
        }
        if (data.user) {
          const nextUser = {
            id: String(telegramUser.id),
            first_name: data.user.first_name || telegramUser.first_name,
            username: data.user.username || telegramUser.username || telegramUser.first_name,
            photo_url: photoUrl,
            is_premium: data.user.is_premium || false,
            credits: data.user.credits || 0,
            is_admin: data.user.is_admin || false,
          };
          setUser(nextUser);
          try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
          setUserProfileHydrated(true);
        }
        // Only set logged in if we have a token
        if (data.access_token) {
          setEngineState({
            autoModeEnabled: true,
            autoModeLocked: false,
            autoModeLockReason: null,
            tradingMode: 'swing',
            stackMentorActive: true,
            riskMode: 'moderate',
            isActive: true,
            current_balance: 0,
            total_profit: 0,
          });
          setRealPositions([]);
          setRealPnl(0);
          setIsLoggedIn(true);
        } else {
          console.error('[Auth] Login failed: no token received');
          alert('Login failed: no access token received. Please try again.');
        }
      } else {
        const errText = await resp.text().catch(() => '');
        console.error('[Auth] Backend auth failed:', resp.status, errText);
        if (resp.status === 502) {
          alert('Login failed (502): backend is temporarily unavailable. Please try again in a moment.');
        } else {
          alert(`Login failed (${resp.status}). Please try again.`);
        }
      }
    } catch (err) {
      console.error('[Auth] Network error:', err);
      // Try fallback base URL
      try {
        const resp2 = await fetch(`${_FALLBACK_BASE}/auth/telegram`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(telegramUser),
        });
        if (resp2.ok) {
          const data = await resp2.json();
          if (data.access_token) {
            _runtimeToken = data.access_token;
            _resolvedBase = _FALLBACK_BASE;
            localStorage.setItem('cm_token', data.access_token);
            if (data.user) {
              const nextUser = { id: String(telegramUser.id), first_name: data.user.first_name || telegramUser.first_name, username: data.user.username || telegramUser.username || telegramUser.first_name, photo_url: photoUrl, is_premium: data.user.is_premium || false, credits: data.user.credits || 0, is_admin: data.user.is_admin || false };
              setUser(nextUser);
              try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
              setUserProfileHydrated(true);
            }
            setEngineState({
              autoModeEnabled: true,
              autoModeLocked: false,
              autoModeLockReason: null,
              tradingMode: 'swing',
              stackMentorActive: true,
              riskMode: 'moderate',
              isActive: true,
              current_balance: 0,
              total_profit: 0,
            });
            setRealPositions([]);
            setRealPnl(0);
            setIsLoggedIn(true);
            return;
          }
        }
      } catch {}
      alert('Login failed: unable to reach the server. Please try again.');
    }
  };

  // Expose callback untuk Telegram widget
  useEffect(() => {
    window.onTelegramAuth = handleTelegramLogin;

    // Inject Telegram Login Widget script
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', 'CryptoMentorAI_bot');
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '10');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;
    const container = document.getElementById('tg-widget-root');
    if (container && !container.hasChildNodes()) {
      container.appendChild(script);
    }
  }, []);

  const handleLogout = () => {
    _runtimeToken = null;
    try { localStorage.removeItem('cm_user'); localStorage.removeItem('cm_token'); } catch {}
    prevPositionIdsRef.current = new Set();
    positionsBaselineSetRef.current = false;
    setIsLoggedIn(false);
    setUser(null);
    setBotRunning(false);
    setVerStatus(null);
    setVerLoading(true);
    setPortfolioLoaded(false);
    setConnectorStatus({ linked: null, online: null, error: null });
    setUserProfileHydrated(false);
  };
  const navigateTo = (tab) => { setActiveTab(tab); setIsMobileMenuOpen(false); };
  const handleBotConnected = () => setShowBotStartModal(true);

  const callEngine = async (action) => {
    setBotBusy(true);
    setBotError(null);
    try {
      const resp = await apiFetch(`/dashboard/engine/${action}`, { method: 'POST' });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(data.detail || `Failed to ${action} engine`);
      setBotRunning(!!data.running);
      return true;
    } catch (e) {
      setBotError(e.message);
      return false;
    } finally {
      setBotBusy(false);
    }
  };

  const handleStartBot = async () => {
    const ok = await callEngine('start');
    if (ok) setShowBotStartModal(false);
  };
  const handleCancelStart = () => setShowBotStartModal(false);
  const handleToggleBot = () => callEngine(botRunning ? 'stop' : 'start');

  const applyEngineSnapshot = (engine = {}) => {
    if (!engine || typeof engine !== 'object') return;
    const has = (key) => Object.prototype.hasOwnProperty.call(engine, key);
    setEngineState(prev => {
      const tradingMode = engine.trading_mode || prev.tradingMode || 'swing';
      const autoModeLocked = has('auto_mode_locked')
        ? !!engine.auto_mode_locked
        : tradingMode === 'mixed';
      const autoModeEnabledRaw = has('auto_mode_enabled')
        ? !!engine.auto_mode_enabled
        : !!prev.autoModeEnabled;
      const autoModeEnabled = autoModeLocked ? false : autoModeEnabledRaw;
      const lockReason = autoModeLocked
        ? (engine.auto_mode_lock_reason || prev.autoModeLockReason || MIXED_AUTO_LOCK_REASON)
        : null;
      const stackMentorActive = has('stackmentor_enabled')
        ? !!engine.stackmentor_enabled
        : (has('stackmentor_active') ? !!engine.stackmentor_active : !!prev.stackMentorActive);
      return {
        ...prev,
        tradingMode,
        autoModeEnabled,
        autoModeLocked,
        autoModeLockReason: lockReason,
        stackMentorActive,
        riskMode: engine.risk_mode || prev.riskMode,
        isActive: has('is_active') ? !!engine.is_active : prev.isActive,
        current_balance: has('current_balance') ? engine.current_balance : prev.current_balance,
        total_profit: has('total_profit') ? engine.total_profit : prev.total_profit,
      };
    });
  };

  const applyEngineControl = async ({ key, endpoint, body, fallbackError }) => {
    setEngineControlBusy(prev => ({ ...prev, [key]: true }));
    setEngineControlError(null);
    try {
      const resp = await apiFetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!resp.ok) {
        const msg = await readApiErrorMessage(resp, fallbackError);
        throw new Error(msg);
      }
      const data = await resp.json().catch(() => ({}));
      if (data?.engine) applyEngineSnapshot(data.engine);
      return data;
    } catch (e) {
      setEngineControlError(e.message || fallbackError);
      return null;
    } finally {
      setEngineControlBusy(prev => ({ ...prev, [key]: false }));
    }
  };

  const handleToggleAutoMode = async () => {
    const locked = !!engineState.autoModeLocked || engineState.tradingMode === 'mixed';
    if (locked || engineControlBusy.autoMode || engineControlBusy.mode) return;
    await applyEngineControl({
      key: 'autoMode',
      endpoint: '/dashboard/engine/auto-mode',
      body: { enabled: !engineState.autoModeEnabled },
      fallbackError: 'Failed to update Auto Mode',
    });
  };

  const handleSelectTradingMode = async (tradingMode) => {
    if (engineControlBusy.mode || engineControlBusy.autoMode) return;
    await applyEngineControl({
      key: 'mode',
      endpoint: '/dashboard/engine/mode',
      body: { trading_mode: tradingMode },
      fallbackError: 'Failed to switch trading mode',
    });
  };

  const handleToggleStackMentor = async () => {
    if (engineControlBusy.stackMentor) return;
    await applyEngineControl({
      key: 'stackMentor',
      endpoint: '/dashboard/engine/stackmentor',
      body: { enabled: !engineState.stackMentorActive },
      fallbackError: 'Failed to update StackMentor preference',
    });
  };

  const updateOneClickRisk = async (rawRisk) => {
    const normalized = normalizeOneClickRisk(rawRisk);
    const previous = normalizeOneClickRisk(riskSettings?.risk_per_trade ?? oneClickRiskPct);
    setOneClickRiskPct(normalized);
    setRiskSettings(prev => ({ ...prev, loading: true, error: null, risk_per_trade: normalized }));
    try {
      const resp = await apiFetch('/dashboard/settings/risk', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ risk_per_trade: normalized, scope: 'one_click' }),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) {
        throw new Error(data.detail || `Error ${resp.status}`);
      }
      const accepted = normalizeOneClickRisk(data?.one_click_risk_per_trade ?? data?.risk_per_trade ?? normalized);
      setOneClickRiskPct(accepted);
      setRiskSettings(prev => ({
        ...prev,
        risk_per_trade: normalizeAutoRisk(data?.risk_per_trade ?? prev.risk_per_trade ?? accepted),
        risk_policy: data.risk_policy || prev.risk_policy || null,
        one_click_risk_policy: data.one_click_risk_policy || prev.one_click_risk_policy || null,
        loading: false,
        error: null,
      }));
    } catch (e) {
      setOneClickRiskPct(previous);
      setRiskSettings(prev => ({
        ...prev,
        risk_per_trade: previous,
        loading: false,
        error: e?.message || 'Failed to sync 1-click risk',
      }));
    }
  };

  const closeOneClickPosition = async (position) => {
    const symbol = String(position?.symbol || '').replace('/', '');
    const side = String(position?.side || position?.sideRaw || '').toUpperCase();
    if (!symbol) throw new Error('Missing position symbol');

    const resp = await apiFetch('/bitunix/positions/close', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, side, source: '1_click' }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.detail || `HTTP ${resp.status}`);

    // Optimistic UI: remove the just-closed card while polling catches up.
    setRealPositions((prev) => prev.filter((p) => String(p.id) !== String(position.id)));
    return data;
  };

  // Fetch risk settings (including LIVE equity from Bitunix)
  const fetchRiskSettings = async () => {
    try {
      const resp = await apiFetch('/dashboard/settings');
      if (resp.ok) {
        const data = await resp.json();
        const syncedRisk = normalizeOneClickRisk(data.one_click_risk_per_trade || data.risk_per_trade || 3);
        setRiskSettings({
          risk_per_trade: normalizeAutoRisk(data.risk_per_trade || 3),
          leverage: data.leverage || 10,
          leverage_baseline: data.leverage_baseline ?? data.leverage ?? 10,
          leverage_mode: data.leverage_mode || 'auto_max_pair',
          leverage_note: data.leverage_note || 'AutoTrade executes with max leverage allowed for each pair.',
          leverage_range: data.leverage_range || { min: 1, max: 200 },
          margin_mode: data.margin_mode || 'cross',
          equity: data.equity || 0,
          balance: data.balance || 0,        // free/available only
          frozen: data.frozen || 0,          // locked in positions
          unrealized_pnl: data.unrealized_pnl || 0,
          risk_policy: data.risk_policy || null,
          one_click_risk_policy: data.one_click_risk_policy || null,
          loading: false,
          error: null,
        });
        setOneClickRiskPct(syncedRisk);
      } else {
        // Even on error, unblock the buttons
        setRiskSettings(prev => ({ ...prev, loading: false }));
      }
    } catch (e) {
      console.error('Failed to fetch risk settings:', e);
      setRiskSettings(prev => ({ ...prev, loading: false }));
    }
  };

  // Update risk setting
  const updateRiskSetting = async (newRisk) => {
    const minPolicy = Number(riskSettings?.risk_policy?.min_pct);
    const minRiskByEquity = Math.max(
      getAutoRiskFloorByEquity(riskSettings?.equity),
      Number.isFinite(minPolicy) ? minPolicy : 0.25
    );
    const effectiveRisk = Math.max(minRiskByEquity, normalizeAutoRisk(newRisk));
    setRiskSettings(prev => ({ ...prev, loading: true, error: null }));
    try {
      const resp = await apiFetch('/dashboard/settings/risk', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ risk_per_trade: effectiveRisk }),
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok) {
        const acceptedRisk = normalizeOneClickRisk(data.one_click_risk_per_trade ?? data.risk_per_trade ?? effectiveRisk);
        setRiskSettings(prev => ({
          ...prev,
          risk_per_trade: normalizeAutoRisk(data.risk_per_trade ?? effectiveRisk),
          risk_policy: data.risk_policy || prev.risk_policy || null,
          one_click_risk_policy: data.one_click_risk_policy || prev.one_click_risk_policy || null,
          loading: false,
          error: null,
        }));
        setOneClickRiskPct(acceptedRisk);
      } else {
        console.error('Failed to update risk setting:', resp.status, data);
        setRiskSettings(prev => ({
          ...prev,
          loading: false,
          error: data.detail || `Error ${resp.status}`,
        }));
      }
    } catch (e) {
      console.error('Error updating risk setting:', e);
      setRiskSettings(prev => ({ ...prev, loading: false, error: e.message }));
    }
  };

  // Update leverage setting
  const updateLeverageSetting = async (newLeverage) => {
    setRiskSettings(prev => ({ ...prev, loading: true, error: null }));
    try {
      const resp = await apiFetch('/dashboard/settings/leverage', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ leverage: newLeverage }),
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok) {
        setRiskSettings(prev => ({
          ...prev,
          leverage: data.leverage ?? newLeverage,
          leverage_baseline: data.leverage_baseline ?? data.leverage ?? newLeverage,
          leverage_mode: data.leverage_mode || prev.leverage_mode || 'auto_max_pair',
          loading: false,
          error: null,
        }));
      } else {
        setRiskSettings(prev => ({
          ...prev,
          loading: false,
          error: data.detail || `Error ${resp.status}`,
        }));
      }
    } catch (e) {
      console.error('Error updating leverage setting:', e);
      setRiskSettings(prev => ({ ...prev, loading: false, error: e.message }));
    }
  };

  // Update margin mode setting
  const updateMarginModeSetting = async (newMode) => {
    setRiskSettings(prev => ({ ...prev, loading: true, error: null }));
    try {
      const resp = await apiFetch('/dashboard/settings/margin-mode', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ margin_mode: newMode }),
      });
      const data = await resp.json().catch(() => ({}));
      if (resp.ok) {
        setRiskSettings(prev => ({
          ...prev,
          margin_mode: data.margin_mode ?? newMode,
          loading: false,
          error: null,
        }));
      } else {
        setRiskSettings(prev => ({
          ...prev,
          loading: false,
          error: data.detail || `Error ${resp.status}`,
        }));
      }
    } catch (e) {
      console.error('Error updating margin mode setting:', e);
      setRiskSettings(prev => ({ ...prev, loading: false, error: e.message }));
    }
  };

  // Hydrate engine running state on login
  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;
    apiFetch('/dashboard/engine/state')
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d || cancelled) return;
        setBotRunning(!!d.running);
        if (d.engine) applyEngineSnapshot(d.engine);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [isLoggedIn]);

  // Fetch risk settings on login
  useEffect(() => {
    if (!isLoggedIn) return;
    fetchRiskSettings();
  }, [isLoggedIn]);

  const applyReferralContext = (next, opts = {}) => {
    const allowDowngrade = !!opts.allowDowngrade;
    setReferralContext((prev) => {
      const prevCode = sanitizeCommunityCode(prev?.community_code);
      const nextCode = sanitizeCommunityCode(next?.community_code);
      const prevSource = prev?.ref_source === 'dynamic' ? 'dynamic' : 'fallback';
      const nextSource = next?.ref_source === 'dynamic' ? 'dynamic' : 'fallback';
      const sameCode = !!prevCode && !!nextCode && prevCode === nextCode;
      if (!allowDowngrade && prevSource === 'dynamic' && nextSource === 'fallback' && (sameCode || !nextCode)) {
        return prev;
      }
      return {
        bitunix_referral_url: next?.bitunix_referral_url || FALLBACK_REFERRAL_URL,
        ref_source: nextSource,
        community_code: nextCode || null,
      };
    });
  };

  const fetchReferralContext = async (codeOverride = null) => {
    const code = String(codeOverride ?? refCode ?? '').trim().toLowerCase();
    const reqSeq = ++referralReqSeqRef.current;
    try {
      const qs = code ? `?community_code=${encodeURIComponent(code)}` : '';
      const resp = await apiFetch(`/user/referral-context${qs}`);
      if (!resp.ok) return;
      const data = await resp.json();
      // Ignore stale responses so older fallback replies can't overwrite newer partner replies.
      if (reqSeq !== referralReqSeqRef.current) return;
      applyReferralContext({
        bitunix_referral_url: data.bitunix_referral_url || FALLBACK_REFERRAL_URL,
        ref_source: data.ref_source || 'fallback',
        community_code: data.community_code || code || null,
      });
      if (data.community_code) {
        const normalized = String(data.community_code).toLowerCase();
        setRefCode(normalized);
        try { localStorage.setItem('cm_ref', normalized); } catch {}
      }
    } catch (err) {
      console.warn('[Referral] Context fetch failed:', err);
    }
  };

  // Fetch verification status on login
  const fetchVerStatus = async () => {
    if (!isLoggedIn) { setVerLoading(false); return; }
    try {
      const resp = await apiFetch('/user/verification-status');
      if (resp.status === 401) {
        // Token expired — force logout and show login screen
        try { localStorage.removeItem('cm_user'); localStorage.removeItem('cm_token'); } catch {}
        setIsLoggedIn(false);
        setUser(null);
        setVerStatus(null);
        return;
      }
      if (resp.ok) {
        const data = await resp.json();
        setVerStatus(data);
        if (data.community_code) {
          const normalized = String(data.community_code).toLowerCase();
          setRefCode(normalized);
          try { localStorage.setItem('cm_ref', normalized); } catch {}
        }
        // Keep dynamic source sticky for the active session unless code is explicitly cleared.
        if (data.bitunix_referral_url) {
          applyReferralContext({
            bitunix_referral_url: data.bitunix_referral_url,
            ref_source: data.ref_source || 'fallback',
            community_code: data.community_code || null,
          });
        }
        setBootIssue(null);
      } else {
        // Fail closed on backend/status errors.
        setVerStatus({ status: 'unknown' });
        setBootIssue(`Session check failed (HTTP ${resp.status}).`);
      }
    } catch (err) {
      console.error('[Verification] Failed:', err);
      // Fail closed on network errors.
      setVerStatus({ status: 'unknown' });
      setBootIssue(`Network error while checking access: ${err.message}`);
    } finally {
      setVerLoading(false);
    }
  };

  useEffect(() => {
    // Reset all session state on login/logout to prevent stale data bypass
    if (isLoggedIn) {
      setVerStatus(null);
      setVerLoading(true);
      setBootIssue(null);
      setPortfolioLoaded(false);
      setConnectorStatus({ linked: null, online: null, error: null });
    }
    fetchVerStatus();
  }, [isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn) {
      setUserProfileHydrated(false);
      return;
    }
    let ignore = false;
    const hydrateUserProfile = async () => {
      try {
        const resp = await apiFetch('/user/me');
        if (!resp.ok) throw new Error(await readApiErrorMessage(resp, 'Failed to load user profile'));
        const data = await resp.json();
        if (ignore) return;
        setUser((prev) => {
          const nextUser = {
            ...(prev || {}),
            ...data,
            id: String(data.telegram_id || data.id || prev?.id || ''),
            first_name: data.first_name || prev?.first_name || 'User',
            username: String(data.username || prev?.username || 'user').replace(/^@/, ''),
            photo_url: prev?.photo_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(data.first_name || prev?.first_name || 'User')}&background=1f2937&color=fff&bold=true`,
            credits: Number(data.credits || 0),
            is_premium: Boolean(data.is_premium || false),
            is_lifetime: Boolean(data.is_lifetime || false),
            is_admin: Boolean(data.is_admin || false),
          };
          try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
          return nextUser;
        });
      } catch (err) {
        console.warn('[Profile] hydration failed:', err?.message || err);
      } finally {
        if (!ignore) setUserProfileHydrated(true);
      }
    };
    hydrateUserProfile();
    return () => { ignore = true; };
  }, [isLoggedIn]);

  // Frontend update watcher: show a small popup when a newer bundle is live.
  useEffect(() => {
    let cancelled = false;

    const checkLatestVersion = async () => {
      try {
        const r = await fetch(`/release-meta.json?ts=${Date.now()}`, { cache: 'no-store' });
        if (!r.ok) return;
        const meta = await r.json();
        const latest = String(meta?.build_marker || meta?.built_at || '').trim();
        if (!latest || latest === BUILD_MARKER) return;

        let dismissed = '';
        try { dismissed = sessionStorage.getItem(UPDATE_DISMISS_KEY) || ''; } catch {}
        if (dismissed === latest) return;

        if (!cancelled) {
          setUpdateNotice({ visible: true, latest });
        }
      } catch {
        // silent: update checks should never break UI
      }
    };

    checkLatestVersion();
    const id = setInterval(checkLatestVersion, 60 * 1000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    // Skip eager fallback fetch until we know whether a referral code exists.
    // This prevents no-code fallback responses from racing and overriding coded responses.
    if (!refCode) return;
    fetchReferralContext(refCode);
  }, [isLoggedIn, refCode]);

  // Guard against indefinite "Checking access..." screen.
  useEffect(() => {
    if (!isLoggedIn || !verLoading) return;
    const id = setTimeout(() => {
      setBootIssue(prev => prev || 'Taking longer than expected to verify session.');
    }, 10000);
    return () => clearTimeout(id);
  }, [isLoggedIn, verLoading]);

  // Poll verification status every 60s — kicks out users deleted from Supabase
  useEffect(() => {
    if (!isLoggedIn) return;
    const id = setInterval(fetchVerStatus, 60000);
    return () => clearInterval(id);
  }, [isLoggedIn]);

  // Listen for 403 verification_required events — immediately re-check status
  useEffect(() => {
    if (!isLoggedIn) return;
    const handler = () => {
      console.warn('[Auth] 403 received — re-checking verification status');
      fetchVerStatus();
    };
    window.addEventListener('cm:verification_required', handler);
    return () => window.removeEventListener('cm:verification_required', handler);
  }, [isLoggedIn]);

  // Live unrealized PnL + positions polling
  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;
    const load = async () => {
      try {
        const r = await apiFetch('/bitunix/positions');
        if (!r.ok) {
          let detail = `HTTP ${r.status}`;
          try { const e = await r.json(); detail = e.detail || detail; } catch {}
          setConnectorStatus(prev => prev.online === false ? prev : { linked: prev.linked, online: false, error: detail });
          return;
        }
        const d = await r.json();
        if (cancelled) return;
        const positions = (d.positions || []).map((p, i) => {
          const pnlNum = Number(p.pnl ?? p.unrealizedPNL ?? 0);
          const sideRaw = String(p.side || p.positionSide || '').toUpperCase();
          const side = sideRaw === 'BUY' || sideRaw === 'LONG' ? 'LONG' : 'SHORT';
          const symbolRaw = String(p.symbol || p.pair || '—');
          const pairDisplay = symbolRaw.endsWith('USDT')
            ? `${symbolRaw.slice(0, -4)}/USDT`
            : symbolRaw;
          const source = p.source || 'autotrade';
          return {
            id: p.position_id || p.positionId || p.id || `${p.symbol}-${i}`,
            pair: pairDisplay,
            symbol: symbolRaw,
            side,
            sideRaw: p.side || sideRaw,
            source,
            sourceLabel: p.source_label || (source === '1_click' ? '1-Click' : 'AutoTrade'),
            entry: `$${Number(p.entryValue || p.avgOpenPrice || p.entry_price || 0).toLocaleString()}`,
            current: `$${Number(p.markPrice || p.mark_price || p.current_price || p.entry_price || 0).toLocaleString()}`,
            margin: `$${Number(p.margin || p.initialMargin || 0).toLocaleString()}`,
            leverage: `${p.leverage || 0}x`,
            pnl: `${pnlNum >= 0 ? '+' : '-'}$${Math.abs(pnlNum).toFixed(2)}`,
            pnlPercent: '',
            isProfitable: pnlNum >= 0,
            tp: {
              tp1: { price: p.tp_price  ? `$${Number(p.tp_price).toLocaleString()}`  : (p.tp1_price ? `$${Number(p.tp1_price).toLocaleString()}` : ''), hit: !!p.tp1_hit },
              tp2: { price: p.tp2_price ? `$${Number(p.tp2_price).toLocaleString()}` : '', hit: !!p.tp2_hit },
              tp3: { price: p.tp3_price ? `$${Number(p.tp3_price).toLocaleString()}` : '', hit: !!p.tp3_hit },
            },
          };
        });

        const currIds = new Set(positions.map((p) => String(p.id)));
        if (!positionsBaselineSetRef.current) {
          prevPositionIdsRef.current = currIds;
          positionsBaselineSetRef.current = true;
        } else {
          let opened = 0;
          let closed = 0;
          currIds.forEach((id) => {
            if (!prevPositionIdsRef.current.has(id)) opened += 1;
          });
          prevPositionIdsRef.current.forEach((id) => {
            if (!currIds.has(id)) closed += 1;
          });
          if (opened > 0) playTradeSound('open');
          if (closed > 0) playTradeSound('close');
          prevPositionIdsRef.current = currIds;
        }

        setRealPositions(positions);
        setRealPnl(Number(d.total_unrealized_pnl || 0));
      } catch {}
    };
    load();
    const id = setInterval(load, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, [isLoggedIn]);

  // Cumulative PnL (closed trades, last 30d) + balance
  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;
    const load = async () => {
      try {
        const r = await apiFetch('/dashboard/portfolio');
        if (cancelled) return;
        if (!r.ok) {
          // Surface HTTP errors (401 token expired, 502 backend crash, etc.)
          let detail = `HTTP ${r.status}`;
          try { const e = await r.json(); detail = e.detail || detail; } catch {}
          setConnectorStatus({ linked: false, online: false, error: detail });
          if (!cancelled) setPortfolioLoaded(true);
          return;
        }
        const d = await r.json();
        if (cancelled) return;
        if (d.portfolio && typeof d.portfolio.pnl_30d === 'number') {
          setCumulativePnl(d.portfolio.pnl_30d);
          setHasCumulativePnl(true);
        }
        if (d.bitunix) {
          setConnectorStatus({
            linked: !!d.bitunix.linked,
            online: !!d.bitunix.account,
            error: d.bitunix.error || null,
          });
          if (d.bitunix.account) {
            const a = d.bitunix.account;
            const eq = Number(a.available || 0)
              + Number(a.frozen || 0)
              + Number(a.margin || 0)
              + Number(a.total_unrealized_pnl || 0);
            setEquity(eq);
          }
        } else {
          // No bitunix data at all — treat as not linked
          setConnectorStatus(prev => ({ ...prev, linked: prev.linked === null ? false : prev.linked }));
        }
        if (!cancelled) setPortfolioLoaded(true);
        if (d.engine) applyEngineSnapshot(d.engine);
      } catch (err) {
        if (!cancelled) {
          setConnectorStatus({ linked: false, online: false, error: `Network error: ${err.message}` });
          setPortfolioLoaded(true);
        }
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn || !isAdminRoute) return;
    if (!userProfileHydrated) return;
    if (user?.is_admin) return;

    const qs = typeof window !== 'undefined' ? window.location.search : '';
    window.location.replace(qs ? `/${qs}` : '/');
  }, [isLoggedIn, isAdminRoute, userProfileHydrated, user?.is_admin]);

  if (isLoggedIn && isAdminRoute) {
    if (!userProfileHydrated && typeof user?.is_admin === 'undefined') {
      return (
        <div className="min-h-screen bg-[#020202] flex items-center justify-center">
          <div className="text-slate-400 text-sm animate-pulse">Loading admin profile...</div>
        </div>
      );
    }
    if (!user?.is_admin) {
      return <AdminDeniedScreen user={user} onLogout={handleLogout} />;
    }
    return <AdminPanel user={user} apiFetch={apiFetch} onLogout={handleLogout} />;
  }

  // Verification gate — block unverified users from dashboard
  // While loading, show spinner — never let through before we know the status
  if (isLoggedIn && verLoading) {
    if (bootIssue) {
      return (
        <div className="min-h-screen bg-[#020202] flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-[#0a0a0a]/70 border border-rose-500/30 rounded-2xl p-6 text-center">
            <h2 className="text-white text-xl font-black mb-2">Session check issue</h2>
            <p className="text-slate-300 text-sm mb-2">
              We could not complete dashboard access verification.
            </p>
            <p className="text-rose-300 text-xs mb-5">{bootIssue}</p>
            <button
              onClick={() => {
                setVerLoading(true);
                fetchVerStatus();
              }}
              className="w-full bg-cyan-500 text-white font-bold py-2.5 rounded-xl hover:bg-cyan-600 transition-colors mb-2"
            >
              Retry
            </button>
            <button
              onClick={handleLogout}
              className="w-full bg-white/10 text-slate-200 font-bold py-2.5 rounded-xl hover:bg-white/20 transition-colors"
            >
              Reset Session
            </button>
          </div>
        </div>
      );
    }
    return (
      <div className="min-h-screen bg-[#020202] flex items-center justify-center">
        <div className="text-slate-400 text-sm animate-pulse">Checking access...</div>
      </div>
    );
  }

  if (isLoggedIn && !verLoading) {
    if (!verStatus || verStatus.status === 'none') {
      return <GatekeeperScreen
        user={user}
        referralUrl={referralContext.bitunix_referral_url}
        referralSource={referralContext.ref_source}
        referralCode={referralContext.community_code || refCode || null}
        onSubmitUID={async (uid) => {
          try {
            const ref = refCode || localStorage.getItem('cm_ref');
            const resp = await apiFetch('/user/submit-uid', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ uid, community_code: ref }),
            });
            if (resp.ok) {
              setVerStatus({ status: 'pending' });
              return { ok: true };
            }
            const err = await resp.json().catch(() => ({}));
            return { ok: false, error: err.detail || 'Failed to submit UID' };
          } catch (e) {
            return { ok: false, error: e.message || 'Network error' };
          }
        }}
        onLogout={handleLogout}
      />;
    }
    if (verStatus.status === 'pending' || verStatus.status === 'pending_verification') {
      return <VerificationPendingScreen onRefresh={fetchVerStatus} onLogout={handleLogout} />;
    }
    if (verStatus.status === 'rejected' || verStatus.status === 'uid_rejected') {
      return <RejectedScreen
        referralUrl={referralContext.bitunix_referral_url}
        referralSource={referralContext.ref_source}
        referralCode={referralContext.community_code || refCode || null}
        onResubmit={async (uid) => {
          try {
            const ref = refCode || localStorage.getItem('cm_ref');
            const resp = await apiFetch('/user/submit-uid', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ uid, community_code: ref }),
            });
            if (resp.ok) { setVerStatus({ status: 'pending' }); return { ok: true }; }
            const err = await resp.json().catch(() => ({}));
            return { ok: false, error: err.detail || 'Failed to submit UID' };
          } catch (e) { return { ok: false, error: e.message || 'Network error' }; }
        }}
        onLogout={handleLogout}
      />;
    }
    // approved only — wait for portfolio data, then check API key
    const isVerified = verStatus?.status === 'approved' || verStatus?.status === 'uid_verified' || verStatus?.status === 'active';
    if (!isVerified) {
      // Any unrecognized or unhandled status — block access, show generic pending screen
      return <VerificationPendingScreen onRefresh={fetchVerStatus} onLogout={handleLogout} />;
    }
    if (!portfolioLoaded) {
      return (
        <div className="min-h-screen bg-[#020202] flex items-center justify-center">
          <div className="text-slate-400 text-sm animate-pulse">Loading your account...</div>
        </div>
      );
    }
    if (connectorStatus.linked === false) {
      return <OnboardingWizard onComplete={() => {
        setPortfolioLoaded(false);
        fetchVerStatus();
        fetchRiskSettings();
        setActiveTab('portfolio');
      }} onLogout={handleLogout} />;
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-[#020202] flex flex-col items-center justify-center p-4 text-slate-200 font-sans relative overflow-hidden selection:bg-fuchsia-500/30">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] z-0 opacity-50" />
        <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-fuchsia-600/20 blur-[100px] md:blur-[150px] pointer-events-none animate-pulse z-0" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-cyan-600/20 blur-[100px] md:blur-[150px] pointer-events-none z-0" />
        <div className="max-w-md w-full bg-[#0a0a0a]/60 backdrop-blur-3xl border border-white/10 rounded-[2rem] md:rounded-[2.5rem] shadow-[0_0_50px_rgba(0,0,0,0.8)] p-8 md:p-10 text-center relative z-10 group hover:border-white/20 transition-all duration-500">
          <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent rounded-[2rem] md:rounded-[2.5rem] pointer-events-none" />
          <div className="w-20 h-20 md:w-24 md:h-24 rounded-3xl md:rounded-[2rem] bg-gradient-to-tr from-fuchsia-500 via-purple-500 to-cyan-500 p-[1px] mx-auto mb-8 shadow-[0_0_30px_rgba(217,70,239,0.3)] rotate-3 group-hover:rotate-6 transition-transform duration-500">
            <div className="w-full h-full bg-[#050505] rounded-[23px] md:rounded-[31px] flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent" />
              <Bot size={40} className="text-white relative z-10" />
            </div>
          </div>
          <h1 className="text-3xl md:text-4xl font-black mb-3 text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 via-purple-400 to-cyan-400 tracking-tight">CryptoMentor AI</h1>
          <p className="text-cyan-400 font-bold tracking-[0.2em] uppercase text-[10px] md:text-xs mb-8 drop-shadow-[0_0_5px_rgba(6,182,212,0.8)]">V4.0 AutoTrade Engine</p>
          <div className="bg-[#050505]/80 p-5 md:p-6 rounded-2xl md:rounded-3xl border border-white/5 mb-8 text-xs md:text-sm text-left space-y-4 shadow-inner">
            <div className="flex items-start gap-3"><div className="p-1.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 mt-0.5 shrink-0"><Layers size={14} className="text-cyan-400" /></div><p className="text-slate-300 font-medium leading-relaxed">Integrated <strong className="text-white">StackMentor</strong> 3-tier Take Profit tracking.</p></div>
            <div className="flex items-start gap-3"><div className="p-1.5 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20 mt-0.5 shrink-0"><RefreshCw size={14} className="text-fuchsia-400" /></div><p className="text-slate-300 font-medium leading-relaxed">Auto Mode Switching <span className="text-slate-500 text-[10px] font-bold">(Scalping ⇌ Swing)</span> based on sentiment.</p></div>
            <div className="flex items-start gap-3"><div className="p-1.5 rounded-xl bg-lime-500/10 border border-lime-500/20 mt-0.5 shrink-0"><CheckCircle2 size={14} className="text-lime-400" /></div><p className="text-slate-300 font-medium leading-relaxed">Exclusive support for Bitunix.</p></div>
          </div>
          {/* Telegram Login Widget */}
          <div id="tg-widget-root" className="flex justify-center min-h-[50px] items-center" />        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#020202] text-slate-200 font-sans flex flex-col relative overflow-x-hidden selection:bg-cyan-500/30">
      <div className="fixed inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px] z-0 pointer-events-none" />
      <div className="fixed top-[-10%] left-[-20%] w-[60vw] h-[60vw] rounded-full bg-violet-600/10 blur-[100px] pointer-events-none z-0" />
      <div className="fixed bottom-[-10%] right-[-20%] w-[60vw] h-[60vw] rounded-full bg-cyan-600/10 blur-[100px] pointer-events-none z-0" />

      {/* PROFIT TICKER — sticky top, auto-hide on mobile scroll down */}
      <TickerWrapper />


      {/* MOBILE TOP BAR */}
      <div className="md:hidden flex items-center justify-between p-4 bg-[#0a0a0a]/90 backdrop-blur-xl border-b border-white/5 sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-fuchsia-500 via-purple-500 to-cyan-500 p-[1px]"><div className="w-full h-full bg-[#050505] rounded-[11px] flex items-center justify-center"><Bot size={18} className="text-white" /></div></div>
          <h1 className="text-lg font-black text-white tracking-tight">CryptoMentor</h1>
        </div>
        <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="p-2 bg-white/5 border border-white/10 rounded-lg text-white hover:bg-white/10 transition-colors">
          {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {showBotStartModal && <BotStartModal onStart={handleStartBot} onCancel={handleCancelStart} />}

      <div className="flex flex-1 overflow-x-hidden relative z-10">
        {isMobileMenuOpen && <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden" onClick={() => setIsMobileMenuOpen(false)} />}

        {/* SIDEBAR */}
        <aside className={`fixed top-[100px] bottom-0 md:inset-y-0 left-0 z-50 w-[280px] md:w-[320px] md:m-6 md:mr-0 bg-[#0a0a0a]/95 md:bg-[#0a0a0a]/80 backdrop-blur-3xl border-r md:border border-white/10 md:rounded-[2.5rem] flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.5)] transition-transform duration-300 ease-in-out transform ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 md:relative md:h-[calc(100vh-3rem)]`}>
          <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />
          <div className="hidden md:flex p-8 items-center gap-4 relative z-10 border-b border-white/5">
            <div className="w-14 h-14 rounded-[1.25rem] bg-gradient-to-tr from-fuchsia-500 via-purple-500 to-cyan-500 p-[1px] shadow-[0_0_20px_rgba(217,70,239,0.3)]"><div className="w-full h-full bg-[#050505] rounded-[19px] flex items-center justify-center"><Bot size={28} className="text-white" /></div></div>
            <div><h1 className="text-2xl font-black text-white tracking-tight leading-tight">CryptoMentor AI</h1><p className="text-cyan-400 text-xs font-bold tracking-[0.2em] uppercase mt-0.5">Your virtual cockpit</p></div>
          </div>
          <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto py-6 relative z-10 custom-scrollbar">
            <p className="px-4 text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">AutoTrade Hub</p>
            <NavItem icon={<Activity size={20} />} label="Portfolio Status" active={activeTab === 'portfolio'} onClick={() => navigateTo('portfolio')} />
            <NavItem icon={<Cpu size={20} />} label="Engine Controls" active={activeTab === 'engine'} onClick={() => navigateTo('engine')} />
            <NavItem icon={<Settings size={20} />} label="API Bridges" active={activeTab === 'settings'} onClick={() => navigateTo('settings')} />
            <p className="px-4 text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 mt-6">Ecosystem</p>
            <NavItem icon={<Radio size={20} />} label="Signals & Market" active={activeTab === 'signals'} onClick={() => navigateTo('signals')} badge={user.is_premium ? "PRO" : "FREE"} />
            <NavItem icon={<Users size={20} />} label="Referral" active={activeTab === 'referral'} onClick={() => navigateTo('referral')} />
          </nav>

          {/* ── Social Proof Ticker ── */}
          <SidebarTicker />

          <div className="p-5 md:p-6 mt-auto relative z-10 border-t border-white/5">
            <div className="flex items-center gap-3 p-3 rounded-[1.5rem] bg-white/[0.03] border border-white/5 mb-4">
              <div className="relative shrink-0">
                <img src={user.photo_url} alt="Profile" className="w-10 h-10 rounded-[1rem] object-cover ring-2 ring-fuchsia-500/30" />
                {user.is_premium && <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-tr from-fuchsia-500 to-cyan-500 rounded-full border-2 border-[#0a0a0a] flex items-center justify-center"><span className="text-[6px] text-white font-black">PRO</span></div>}
              </div>
              <div className="overflow-hidden flex-1"><p className="text-sm font-bold text-white truncate">{user.first_name}</p><p className="text-xs text-slate-400 truncate">@{user.username}</p></div>
            </div>
            {/* Bot Start/Stop Button */}
            <button
              onClick={handleToggleBot}
              disabled={botBusy}
              className={`w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-black rounded-xl transition-all mb-3 disabled:opacity-50 ${
                botRunning
                  ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25'
                  : 'bg-lime-500/15 text-lime-400 border border-lime-500/30 hover:bg-lime-500/25'
              }`}
            >
              {botBusy ? '...' : (botRunning ? <><StopCircle size={16} /> Stop Bot</> : <><Power size={16} /> Start Bot</>)}
            </button>
            {botError && <p className="text-[10px] text-rose-400 mb-2 text-center">{botError}</p>}
            <button onClick={handleLogout} className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold text-rose-400 hover:text-white hover:bg-rose-500/90 border border-rose-500/20 rounded-xl transition-all"><LogOut size={16} /> Disconnect</button>
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="flex-1 min-w-0 overflow-y-auto p-4 md:p-8 lg:p-10 w-full relative z-0 pb-20 md:pb-10 custom-scrollbar">
          {activeTab === 'portfolio' && <PortfolioTab positions={realPositions.length > 0 ? realPositions : []} engineState={engineState} unrealizedPnl={realPnl} cumulativePnl={cumulativePnl} equity={equity} hasRealData={realPositions.length > 0} hasCumulative={hasCumulativePnl} botRunning={botRunning} onToggleBot={handleToggleBot} botBusy={botBusy} connectorStatus={connectorStatus} onCloseOneClickPosition={closeOneClickPosition} />}
          {activeTab === 'engine' && (
            <EngineTab
              engineState={engineState}
              botRunning={botRunning}
              onToggleBot={handleToggleBot}
              onToggleAutoMode={handleToggleAutoMode}
              onSelectTradingMode={handleSelectTradingMode}
              onToggleStackMentor={handleToggleStackMentor}
              controlBusy={engineControlBusy}
              controlError={engineControlError}
              riskSettings={riskSettings}
              onUpdateRisk={updateRiskSetting}
              onUpdateLeverage={updateLeverageSetting}
              onUpdateMarginMode={updateMarginModeSetting}
            />
          )}
          {activeTab === 'settings' && <SettingsTab onBotConnected={handleBotConnected} />}
          {activeTab === 'signals' && (
            <SignalsTab
              user={user}
              riskSettings={riskSettings}
              oneClickRiskPct={oneClickRiskPct}
              onUpdateOneClickRisk={updateOneClickRisk}
              focusedSignalId={deepLinkContext?.signal_id || null}
              focusAction={deepLinkContext?.action || null}
            />
          )}
          {activeTab === 'referral' && <ReferralTab user={user} />}
          <div className="mt-6 text-center text-[10px] text-slate-600 font-mono">build {BUILD_MARKER}</div>
        </main>
      </div>

      {updateNotice.visible && (
        <UpdateAvailablePopup
          latest={updateNotice.latest}
          onRefresh={() => window.location.reload()}
          onDismiss={() => {
            try { sessionStorage.setItem(UPDATE_DISMISS_KEY, updateNotice.latest || ''); } catch {}
            setUpdateNotice({ visible: false, latest: updateNotice.latest });
          }}
        />
      )}
    </div>
  );
}

function UpdateAvailablePopup({ latest, onRefresh, onDismiss }) {
  return (
    <div className="fixed bottom-4 right-4 z-[120] w-[300px] max-w-[calc(100vw-2rem)] rounded-2xl border border-cyan-500/35 bg-[#0b0f16]/95 backdrop-blur-xl p-4 shadow-[0_16px_40px_rgba(0,0,0,0.45)]">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 rounded-lg border border-cyan-400/40 bg-cyan-500/15 p-1.5">
          <RefreshCw size={14} className="text-cyan-300" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-white">New version available</p>
          <p className="mt-1 text-xs text-slate-300">A newer web update is ready. Refresh to apply it.</p>
          <p className="mt-1 truncate text-[10px] text-slate-500 font-mono">latest {latest}</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-end gap-2">
        <button onClick={onDismiss} className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-white/10">
          Later
        </button>
        <button onClick={onRefresh} className="rounded-lg border border-cyan-400/50 bg-cyan-500/15 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-500/25">
          Refresh
        </button>
      </div>
    </div>
  );
}

function RiskManagementCard({ riskSettings, onUpdateRisk, onUpdateLeverage, onUpdateMarginMode }) {
  const safeRisk = riskSettings || { risk_per_trade: 3, loading: false, error: null };
  const [autoRiskDraft, setAutoRiskDraft] = useState(null);
  const [autoSliderRisk, setAutoSliderRisk] = useState(null);
  const autoRiskPct = normalizeAutoRisk(safeRisk.risk_per_trade || 3);
  const policyMin = Number(safeRisk?.risk_policy?.min_pct);
  const autoRiskMin = Math.max(
    getAutoRiskFloorByEquity(safeRisk.equity),
    Number.isFinite(policyMin) ? policyMin : 0.25
  );
  const controlAutoRisk = autoSliderRisk !== null ? autoSliderRisk : autoRiskPct;

  const commitAutoRisk = (value) => {
    const normalized = Math.max(autoRiskMin, normalizeAutoRisk(value));
    setAutoSliderRisk(normalized);
    onUpdateRisk(normalized);
  };

  useEffect(() => {
    if (!safeRisk.loading) setAutoSliderRisk(null);
  }, [safeRisk.loading, autoRiskPct]);

  useEffect(() => {
    if (!safeRisk.loading && autoRiskPct < autoRiskMin) {
      onUpdateRisk(autoRiskMin);
    }
  }, [safeRisk.loading, autoRiskPct, autoRiskMin, onUpdateRisk]);

  if (!riskSettings) return null;
  
  return (
    <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-amber-500/30 rounded-[1.5rem] md:rounded-[2.5rem] p-6 md:p-8 relative overflow-hidden h-full">
      <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 blur-[40px] rounded-full pointer-events-none" />
      <div className="flex items-start justify-between mb-6 relative z-10">
        <div>
          <h3 className="text-xl md:text-2xl font-black text-white mb-2">Risk Management</h3>
          <p className="text-slate-400 text-xs md:text-sm font-medium leading-relaxed">Position sizes scale inversely with stop loss distance.</p>
        </div>
        <div className="p-2.5 bg-amber-500/10 rounded-xl border border-amber-500/20"><Target className="text-amber-400 w-6 h-6" /></div>
      </div>

      <div className="space-y-6 relative z-10">
        {/* Risk Level */}
        <div>
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">
            Risk Per Trade ({autoRiskMin.toFixed(2).replace(/\.00$/, '')}% - 10%)
          </p>
          <div className="grid grid-cols-4 gap-2">
            {RISK_OPTIONS.map(risk => (
              (() => {
                const blockedByFloor = risk < autoRiskMin;
                return (
              <button
                key={risk}
                onClick={() => onUpdateRisk(Math.max(risk, autoRiskMin))}
                disabled={riskSettings.loading || blockedByFloor}
                className={`py-2 px-1 rounded-lg font-bold text-[10px] md:text-xs transition-all ${
                  Number(riskSettings.risk_per_trade) === Math.max(risk, autoRiskMin)
                    ? getRiskButtonTone(risk)
                    : risk > 5.0
                      ? 'bg-[#090505] text-amber-300/70 border border-amber-500/15 hover:border-rose-500/35 hover:text-amber-200'
                      : 'bg-[#050505] text-green-300/80 border border-green-500/15 hover:border-green-500/35 hover:text-green-200'
                } disabled:opacity-40`}
              >
                {risk}%
              </button>
                );
              })()
            ))}
          </div>
          <div className="mt-3 bg-white/5 rounded-lg p-2.5">
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">AutoTrade Slider + Numeric Input</p>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={String(autoRiskMin)}
                max="10"
                step="0.25"
                value={Math.max(controlAutoRisk, autoRiskMin)}
                disabled={riskSettings.loading}
                onChange={e => setAutoSliderRisk(parseFloat(e.target.value))}
                onMouseUp={e => commitAutoRisk(e.currentTarget.value)}
                onTouchEnd={e => commitAutoRisk(e.currentTarget.value)}
                className="flex-1 accent-amber-500 disabled:opacity-40"
              />
              <input
                type="number"
                min={String(autoRiskMin)}
                max="10"
                step="0.25"
                value={autoRiskDraft !== null ? autoRiskDraft : Math.max(controlAutoRisk, autoRiskMin)}
                disabled={riskSettings.loading}
                onChange={e => setAutoRiskDraft(e.target.value)}
                onBlur={() => {
                  if (autoRiskDraft !== null) {
                    commitAutoRisk(autoRiskDraft);
                    setAutoRiskDraft(null);
                  }
                }}
                onKeyDown={e => {
                  if (e.key === 'Enter') e.currentTarget.blur();
                  if (e.key === 'Escape') { setAutoRiskDraft(null); e.target.blur(); }
                }}
                className="w-16 px-2 py-1 rounded bg-[#050505] border border-white/10 text-white text-xs font-mono text-center focus:outline-none focus:border-amber-500/50 disabled:opacity-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
              <span className="text-[10px] text-slate-500 font-bold">%</span>
            </div>
          </div>
          {safeRisk.equity > 0 && safeRisk.equity < LOW_EQUITY_THRESHOLD_USD && (
            <p className="text-[10px] mt-2 text-amber-300 font-medium">
              Low equity safeguard: for equity below ${LOW_EQUITY_THRESHOLD_USD}, minimum risk is {LOW_EQUITY_MIN_RISK_PCT}%.
            </p>
          )}
          <p className={`text-[10px] mt-2 font-medium ${riskSettings.risk_per_trade > 5.0 ? 'text-amber-300' : 'text-green-400'}`}>
            {getRiskDescription(riskSettings.risk_per_trade)}
          </p>
          {riskSettings.error && (
            <p className="text-[10px] mt-2 text-rose-400 font-medium">{riskSettings.error}</p>
          )}
        </div>

        {/* Leverage Mode & Margin Mode Row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">Leverage</p>
            <div className="bg-[#050505] p-3 rounded-lg border border-amber-500/25 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">Mode</span>
                <span className="text-[10px] font-black text-amber-300 uppercase tracking-wider">
                  {(riskSettings.leverage_mode || 'auto_max_pair').replaceAll('_', ' ')}
                </span>
              </div>
              <p className="text-xs text-white font-semibold">
                Auto Max Pair Leverage
                <span className="text-slate-400 font-medium ml-1">
                  ({riskSettings.leverage_range?.min ?? 1}x - {riskSettings.leverage_range?.max ?? 20}x)
                </span>
              </p>
              <p className="text-[10px] text-slate-400 leading-relaxed">
                {riskSettings.leverage_note || 'Backend uses max leverage allowed for each pair.'}
              </p>
            </div>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">Margin Mode</p>
            <div className="flex gap-1.5 bg-[#050505] p-1 rounded-lg border border-white/5">
              {['cross', 'isolated'].map(mode => (
                <button
                  key={mode}
                  onClick={() => onUpdateMarginMode(mode)}
                  disabled={riskSettings.loading}
                  className={`flex-1 py-1.5 rounded-md font-bold text-[10px] uppercase transition-all ${
                    (riskSettings.margin_mode || 'cross') === mode
                      ? 'bg-amber-500 text-white'
                      : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {mode.slice(0, 4)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Account Summary */}
        {riskSettings.equity > 0 && (
          <div className="bg-[#050505]/50 border border-white/5 p-4 rounded-xl space-y-2">
            <div className="flex justify-between text-[10px] font-medium uppercase tracking-wider text-slate-500">
              <span>Account Status</span>
              <span className="text-cyan-400 animate-pulse">Live</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-400">Equity</span>
              <span className="text-xs font-black text-white">${riskSettings.equity.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center border-t border-white/5 pt-2">
              <span className="text-xs text-amber-400 font-bold">Dollar Risk</span>
              <span className="text-xs font-black text-amber-400">${(riskSettings.equity * (riskSettings.risk_per_trade / 100)).toFixed(2)}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PortfolioTab({
  positions,
  engineState,
  unrealizedPnl,
  cumulativePnl,
  equity,
  hasRealData,
  hasCumulative,
  botRunning,
  onToggleBot,
  botBusy,
  connectorStatus,
  onCloseOneClickPosition,
}) {
  const pnlAbs = Math.abs(unrealizedPnl).toFixed(2);
  const pnlDisplay = hasRealData ? `${unrealizedPnl >= 0 ? '+' : '-'}$${pnlAbs}` : '$0.00';
  const realizedAbs = Math.abs(cumulativePnl).toFixed(2);
  const realizedDisplay = `${cumulativePnl >= 0 ? '+' : '-'}$${realizedAbs}`;
  const equityDisplay = equity !== null && equity !== undefined ? `$${Number(equity).toFixed(2)}` : '—';

  // Connector status banner helpers
  const cs = connectorStatus || {};
  const showOffline  = cs.linked === false;
  const showError    = cs.linked === true  && cs.online === false;
  const showNetError = cs.linked === null  && cs.online === false && cs.error;
  const autotradePositions = positions.filter((p) => p.source !== '1_click');
  const oneClickPositions = positions.filter((p) => p.source === '1_click');

  return (
    <div className="max-w-6xl w-full mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      {showNetError && (
        <div className="flex items-start gap-3 bg-rose-500/10 border border-rose-500/30 px-4 py-3 rounded-xl text-rose-300 text-sm font-bold">
          <span className="mt-0.5 shrink-0">🔴</span>
          <div>
            <p>Backend unreachable — could not load portfolio data.</p>
            <p className="text-xs font-normal text-rose-400/80 mt-1 font-mono">{cs.error}</p>
            <p className="text-xs font-normal text-rose-400/60 mt-1">The API server may be restarting. Retrying every 5 seconds…</p>
          </div>
        </div>
      )}
      {showOffline && (
        <div className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/30 px-4 py-3 rounded-xl text-amber-300 text-sm font-bold">
          <span>⚠️</span>
          <span>Bitunix API keys not configured. Go to <strong>API Bridges</strong> to link your account.</span>
        </div>
      )}
      {showError && (
        <div className="flex items-start gap-3 bg-rose-500/10 border border-rose-500/30 px-4 py-3 rounded-xl text-rose-300 text-sm font-bold">
          <span className="mt-0.5 shrink-0">🔴</span>
          <div>
            <p>Bitunix connector offline — live data unavailable.</p>
            {cs.error && <p className="text-xs font-normal text-rose-400/80 mt-1 font-mono">{cs.error}</p>}
            <p className="text-xs font-normal text-rose-400/60 mt-1">Check your API keys in <strong>API Bridges</strong> or verify your Bitunix account status.</p>
          </div>
        </div>
      )}
      <header className="mb-8 md:mb-12 flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Portfolio Status</h2>
          <span className="text-slate-400 font-medium text-sm md:text-lg">AI-managed assets overview.</span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-3 bg-white/5 border border-white/10 px-4 py-2.5 rounded-xl backdrop-blur-md">
            <div className="flex flex-col items-end border-r border-white/10 pr-3">
              <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest mb-0.5">Mode</span>
              <span className={`text-xs font-black uppercase tracking-wider ${
                engineState.tradingMode === 'scalping'
                  ? 'text-fuchsia-400'
                  : engineState.tradingMode === 'mixed'
                    ? 'text-amber-300'
                    : 'text-cyan-400'
              }`}>{engineState.tradingMode || 'swing'}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${botRunning ? 'bg-lime-400' : 'bg-slate-600'}`}></span>
                <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${botRunning ? 'bg-lime-400 shadow-[0_0_10px_rgba(163,230,53,0.8)]' : 'bg-slate-600'}`}></span>
              </span>
              <span className={`text-[10px] font-bold tracking-[0.1em] uppercase ${botRunning ? 'text-lime-400' : 'text-slate-500'}`}>{botRunning ? 'Active' : 'Stopped'}</span>
            </div>
          </div>
          <button
            onClick={onToggleBot}
            disabled={botBusy}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm transition-all whitespace-nowrap disabled:opacity-50 ${botRunning ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25' : 'bg-lime-500/15 text-lime-400 border border-lime-500/30 hover:bg-lime-500/25'}`}
          >
            {botBusy ? '...' : botRunning ? <><StopCircle size={15} /> Stop Engine</> : <><Power size={15} /> Start Engine</>}
          </button>
        </div>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 md:gap-6">
        <StatCard title="Account Equity" value={equityDisplay} subtext="Avail + Margin + uPnL" icon={<Wallet className="text-cyan-400 w-6 h-6" />} glowColor="cyan" />
        <StatCard title="Unrealized PnL" value={pnlDisplay} subtext="Live open positions" isPositive={unrealizedPnl >= 0} icon={<Activity className={`w-6 h-6 ${unrealizedPnl >= 0 ? 'text-lime-400' : 'text-rose-400'}`} />} glowColor={unrealizedPnl >= 0 ? 'lime' : 'rose'} />
        <StatCard title="Realized PnL (30d)" value={realizedDisplay} subtext="Closed trades" isPositive={cumulativePnl >= 0} icon={<TrendingUp className="text-fuchsia-400 w-6 h-6" />} glowColor="fuchsia" />
        <StatCard title="Open Positions" value={positions.length.toString()} icon={<Target className="text-cyan-400 w-6 h-6" />} glowColor="cyan" />

      </div>
      <div className="pt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
          <h3 className="text-xl md:text-2xl font-black text-white tracking-tight flex items-center gap-3">Current Opened Positions <span className="px-2.5 py-1 rounded-lg bg-white/10 text-white/60 text-xs font-bold">{positions.length}</span></h3>
          {engineState.stackMentorActive && <div className="w-fit flex items-center gap-2 text-xs font-bold text-fuchsia-400 bg-fuchsia-500/10 px-3 py-1.5 rounded-lg border border-fuchsia-500/20"><Layers size={14} /> STACKMENTOR TRACKING</div>}
        </div>

        {positions.length > 0 ? (
          <div className="space-y-8">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[10px] font-black tracking-widest uppercase text-cyan-300 bg-cyan-500/10 border border-cyan-500/25 px-2.5 py-1 rounded-lg">AutoTrade</span>
                <span className="text-xs text-slate-400">{autotradePositions.length} positions</span>
              </div>
              {autotradePositions.length > 0 ? (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
                  {autotradePositions.map((pos) => (
                    <PositionCard
                      key={pos.id}
                      position={pos}
                      stackMentorActive={engineState.stackMentorActive}
                      isOneClick={false}
                      onCloseOneClickPosition={onCloseOneClickPosition}
                    />
                  ))}
                </div>
              ) : (
                <div className="bg-[#0a0a0a]/50 border border-white/10 rounded-2xl p-4 text-sm text-slate-500">
                  No AutoTrade positions open right now.
                </div>
              )}
            </div>

            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-[10px] font-black tracking-widest uppercase text-amber-300 bg-amber-500/10 border border-amber-500/25 px-2.5 py-1 rounded-lg">1-Click Trade</span>
                <span className="text-xs text-slate-400">{oneClickPositions.length} positions</span>
              </div>
              {oneClickPositions.length > 0 ? (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
                  {oneClickPositions.map((pos) => (
                    <PositionCard
                      key={pos.id}
                      position={pos}
                      stackMentorActive={engineState.stackMentorActive}
                      isOneClick={true}
                      onCloseOneClickPosition={onCloseOneClickPosition}
                    />
                  ))}
                </div>
              ) : (
                <div className="bg-[#0a0a0a]/50 border border-white/10 rounded-2xl p-4 text-sm text-slate-500">
                  No 1-click positions open right now.
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-10 flex flex-col items-center justify-center text-center opacity-80 mt-4">
            <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-4 border border-white/10"><Target className="text-slate-500 w-8 h-8" /></div>
            <h4 className="text-white font-black text-xl mb-2">No Open Positions</h4>
            <p className="text-slate-400 font-medium text-sm">No active trades on Bitunix right now. AutoTrade engine is scanning.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function EngineTab({
  engineState,
  botRunning,
  onToggleBot,
  onToggleAutoMode,
  onSelectTradingMode,
  onToggleStackMentor,
  controlBusy = { autoMode: false, mode: false, stackMentor: false },
  controlError = null,
  riskSettings = {
    risk_per_trade: 3,
    leverage: 10,
    equity: 0,
    balance: 0,
    frozen: 0,
    unrealized_pnl: 0,
    loading: true,
    error: null,
  },
  onUpdateRisk,
  onUpdateLeverage,
  onUpdateMarginMode,
}) {
  const autoModeLocked = !!engineState.autoModeLocked || engineState.tradingMode === 'mixed';
  const autoToggleBusy = !!controlBusy.autoMode;
  const modeBusy = !!controlBusy.mode;
  const stackMentorBusy = !!controlBusy.stackMentor;
  const autoToggleDisabled = autoModeLocked || autoToggleBusy || modeBusy;
  const modeButtonsDisabled = autoToggleBusy || modeBusy;

  return (
    <div className="max-w-4xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Engine Controls</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Configure AutoTrade behavior, StackMentor, Risk management, and Position sizing.</p></header>

      {/* Bot Power Control */}
      <div className={`relative overflow-hidden rounded-[1.5rem] md:rounded-[2.5rem] border p-6 md:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 transition-all duration-500 ${
        botRunning
          ? 'bg-lime-500/5 border-lime-500/40 shadow-[0_0_50px_rgba(163,230,53,0.12)]'
          : 'bg-[#0a0a0a]/60 border-white/10'
      }`}>
        {botRunning && <div className="absolute inset-0 bg-gradient-to-r from-lime-500/5 to-transparent pointer-events-none" />}
        <div className="flex items-center gap-5 relative z-10">
          <div className={`p-4 rounded-2xl border transition-all duration-500 ${
            botRunning ? 'bg-lime-500/15 border-lime-500/30' : 'bg-white/5 border-white/10'
          }`}>
            <Power className={`w-7 h-7 transition-colors duration-300 ${botRunning ? 'text-lime-400' : 'text-slate-500'}`} />
          </div>
          <div>
            <h3 className="text-xl md:text-2xl font-black text-white tracking-tight mb-1">AutoTrade Engine</h3>
            <div className="flex items-center gap-2">
              {botRunning ? (
                <><span className="relative flex h-2 w-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2 w-2 bg-lime-400"></span></span>
                <span className="text-xs font-bold text-lime-400 uppercase tracking-wider">Running — Scanning Markets</span></>
              ) : (
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Stopped — Not Trading</span>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={onToggleBot}
          className={`relative z-10 flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-base transition-all duration-300 shrink-0 ${
            botRunning
              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25 hover:shadow-[0_0_30px_rgba(244,63,94,0.2)]'
              : 'bg-lime-500/15 text-lime-400 border border-lime-500/30 hover:bg-lime-500/25 hover:shadow-[0_0_30px_rgba(163,230,53,0.2)]'
          }`}
        >
          {botRunning ? <><StopCircle size={20} /> Stop Bot</> : <><Power size={20} /> Start Bot</>}
        </button>
      </div>

      {controlError && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl px-4 py-3 text-sm font-semibold text-rose-300">
          {controlError}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl border ${engineState.autoModeEnabled ? 'border-fuchsia-500/50 shadow-[0_0_40px_rgba(217,70,239,0.15)]' : 'border-white/10'} rounded-[1.5rem] md:rounded-[2.5rem] p-6 md:p-8 relative overflow-hidden transition-all duration-500 group`}>
          {engineState.autoModeEnabled && <div className="absolute top-0 right-0 w-32 h-32 bg-fuchsia-500/10 blur-[40px] rounded-full pointer-events-none" />}
          <div className="flex justify-between items-start mb-5 relative z-10">
            <div className="p-2.5 bg-white/5 rounded-xl border border-white/5"><RefreshCw className={engineState.autoModeEnabled ? "text-fuchsia-400 animate-spin-slow w-6 h-6" : "text-slate-500 w-6 h-6"} /></div>
            <button
              onClick={onToggleAutoMode}
              disabled={autoToggleDisabled}
              className={`p-1 -m-1 transition-transform active:scale-90 ${autoToggleDisabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {engineState.autoModeEnabled ? <ToggleRight className="text-fuchsia-500 w-9 h-9" /> : <ToggleLeft className="text-slate-600 w-9 h-9" />}
            </button>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-white mb-2 relative z-10">Auto Mode Switcher</h3>
          <p className="text-slate-400 text-xs md:text-sm font-medium leading-relaxed relative z-10 mb-6">Legacy auto-switch flips between Scalping and Swing. Mixed mode uses per-symbol auto routing and bypasses legacy global flips.</p>
          {autoModeLocked && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 mb-4 relative z-10">
              <p className="text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-1">Locked in Mixed Mode</p>
              <p className="text-xs text-amber-200/80">{engineState.autoModeLockReason || MIXED_AUTO_LOCK_REASON}</p>
            </div>
          )}
          {(autoToggleBusy || modeBusy) && (
            <p className="text-[11px] text-fuchsia-300 font-semibold mb-3 relative z-10">
              {modeBusy ? 'Applying trading mode change...' : 'Applying auto mode preference...'}
            </p>
          )}
          {!engineState.autoModeEnabled && (
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 relative z-10">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">Manual Override</p>
              <div className="flex gap-2">
                <button
                  onClick={() => onSelectTradingMode('scalping')}
                  disabled={modeButtonsDisabled}
                  className={`flex-1 py-3 rounded-lg font-bold text-xs transition-all ${engineState.tradingMode === 'scalping' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-[#050505] text-slate-400 border border-white/5'} ${modeButtonsDisabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  SCALPING
                </button>
                <button
                  onClick={() => onSelectTradingMode('swing')}
                  disabled={modeButtonsDisabled}
                  className={`flex-1 py-3 rounded-lg font-bold text-xs transition-all ${engineState.tradingMode === 'swing' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-[#050505] text-slate-400 border border-white/5'} ${modeButtonsDisabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  SWING
                </button>
                <button
                  onClick={() => onSelectTradingMode('mixed')}
                  disabled={modeButtonsDisabled}
                  className={`flex-1 py-3 rounded-lg font-bold text-xs transition-all ${engineState.tradingMode === 'mixed' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-[#050505] text-slate-400 border border-white/5'} ${modeButtonsDisabled ? 'opacity-60 cursor-not-allowed' : ''}`}
                >
                  MIXED
                </button>
              </div>
            </div>
          )}
        </div>
        <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl border ${engineState.stackMentorActive ? 'border-cyan-500/50 shadow-[0_0_40px_rgba(6,182,212,0.15)]' : 'border-white/10'} rounded-[1.5rem] md:rounded-[2.5rem] p-6 md:p-8 relative overflow-hidden transition-all duration-500 group`}>
          {engineState.stackMentorActive && <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 blur-[40px] rounded-full pointer-events-none" />}
          <div className="flex justify-between items-start mb-5 relative z-10">
            <div className="p-2.5 bg-white/5 rounded-xl border border-white/5"><Layers className={engineState.stackMentorActive ? "text-cyan-400 w-6 h-6" : "text-slate-500 w-6 h-6"} /></div>
            <button
              onClick={onToggleStackMentor}
              disabled={stackMentorBusy}
              className={`p-1 -m-1 transition-transform active:scale-90 ${stackMentorBusy ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {engineState.stackMentorActive ? <ToggleRight className="text-cyan-500 w-9 h-9" /> : <ToggleLeft className="text-slate-600 w-9 h-9" />}
            </button>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-white mb-2 relative z-10">StackMentor Preference</h3>
          <p className="text-slate-400 text-xs md:text-sm font-medium leading-relaxed relative z-10 mb-6">Persists your StackMentor preference from web controls. Runtime execution behavior is unchanged in this release.</p>
          {stackMentorBusy && (
            <p className="text-[11px] text-cyan-300 font-semibold mb-3 relative z-10">Saving StackMentor preference...</p>
          )}
          <div className={`space-y-2.5 relative z-10 transition-all duration-300 ${!engineState.stackMentorActive ? 'opacity-40 grayscale pointer-events-none' : ''}`}>
            {[{label:'Preference ON: stackmentor profile', color:'cyan'},{label:'Preference OFF: keep legacy profile flag', color:'cyan'},{label:'Execution path unchanged in this patch', color:'fuchsia'}].map((tp, i) => (
              <div key={i} className="flex items-center gap-3 bg-[#050505] border border-white/5 p-3 rounded-xl">
                <div className={`w-2.5 h-2.5 rounded-full ${engineState.stackMentorActive ? (tp.color === 'cyan' ? 'bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]' : 'bg-fuchsia-400 shadow-[0_0_8px_rgba(217,70,239,0.8)]') : 'bg-slate-700'}`} />
                <span className="text-xs font-bold text-slate-300">{tp.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Risk Management Card */}

      <RiskManagementCard riskSettings={riskSettings} onUpdateRisk={onUpdateRisk} onUpdateLeverage={onUpdateLeverage} onUpdateMarginMode={onUpdateMarginMode} />
    </div>
  );
}

function PerformanceTab() {
  const [livePerf, setLivePerf] = useState(null);
  const [hoverPoint, setHoverPoint] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await apiFetch('/dashboard/performance');
        if (!r.ok) return;
        const d = await r.json();
        if (!cancelled) setLivePerf(d);
      } catch {}
    };
    load();
    const id = setInterval(load, 10000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const m = livePerf?.metrics;
  const fmtPct = (n) => `${Number(n).toFixed(1)}%`;
  const liveMetrics = m ? {
    sharpe: Number(m.sharpe).toFixed(2),
    maxDd: fmtPct(m.max_drawdown_pct),
    winRate: fmtPct(m.win_rate_pct),
    trades: Number(m.total_trades).toLocaleString(),
    volatility: fmtPct(m.volatility_pct),
  } : { sharpe: '—', maxDd: '—', winRate: '—', trades: '0', volatility: '—' };

  const chartData = (livePerf?.equity_curve && livePerf.equity_curve.length > 0)
    ? livePerf.equity_curve
    : HISTORICAL_DATA;
  const playbookAnalysis = livePerf?.playbook_analysis || null;
  const paPromote = Array.isArray(playbookAnalysis?.promote) ? playbookAnalysis.promote : [];
  const paAvoid = Array.isArray(playbookAnalysis?.avoid) ? playbookAnalysis.avoid : [];
  const paCoverage = playbookAnalysis?.coverage || {};
  const paSampleSize = Number(playbookAnalysis?.sample_size || 0);
  const paSparse = Boolean(playbookAnalysis?.sparse_data);
  const paWinsReasonPct = Number(paCoverage?.wins_with_reasoning_pct || 0);
  const paUsableTagsPct = Number(paCoverage?.closed_with_usable_tags_pct || 0);
  const paWeakMatchPct = Number(paCoverage?.weak_or_missing_playbook_match_wins_pct || 0);

  const formatCluster = (row) => {
    if (!row) return 'No setup data';
    const label = String(row.label || 'Setup');
    const support = Number(row.support || 0);
    const winRatePct = Number(row.win_rate || 0) * 100;
    const expectancy = Number(row.expectancy_usdt || 0);
    const medianR = Number(row.median_r || 0);
    return `${label} • n=${support} • WR ${winRatePct.toFixed(1)}% • Exp ${expectancy >= 0 ? '+' : ''}${expectancy.toFixed(3)} • R ${medianR >= 0 ? '+' : ''}${medianR.toFixed(2)}`;
  };

  const [hoverMetrics, setHoverMetrics] = useState(null);
  const activeMetrics = hoverMetrics || liveMetrics;

  const handleMouseMove = (data) => {
    if (data && data.activePayload && data.activePayload.length) {
      const payload = data.activePayload[0].payload;
      setHoverPoint({ date: payload.date, equity: payload.equity });
      // If chart point carries per-row metrics (legacy mock), use them.
      if (payload.sharpe !== undefined) {
        setHoverMetrics({
          sharpe: payload.sharpe,
          maxDd: payload.maxDd,
          winRate: payload.winRate,
          trades: payload.trades.toLocaleString(),
          volatility: payload.volatility,
        });
      }
    }
  };

  const handleMouseLeave = () => {
    setHoverPoint(null);
    setHoverMetrics(null);
  };

  const equityValues = chartData.map(d => d.equity);
  const yMin = Math.min(...equityValues);
  const yMax = Math.max(...equityValues);
  const yPad = (yMax - yMin) * 0.1 || 1;

  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">PnL Performance</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Advanced metrics and historical analytics.</p></header>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6">
        <MiniStat title="Sharpe" value={activeMetrics.sharpe} subtitle="Risk-Adjusted Return" highlight="text-cyan-400" glow="cyan" />
        <MiniStat title="Max DD" value={activeMetrics.maxDd} subtitle="Historical Peak-to-Trough" highlight="text-rose-400" glow="rose" />
        <MiniStat title="Win Rate" value={activeMetrics.winRate} subtitle={`${activeMetrics.trades} Trades`} highlight="text-lime-400" glow="lime" />
        <MiniStat title="Volatility" value={activeMetrics.volatility} subtitle="Average fluctuation" highlight="text-fuchsia-400" glow="fuchsia" />
      </div>
      <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-white/5 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-8 relative overflow-hidden flex flex-col h-[350px] md:h-[500px] group">
        <div className="absolute top-0 right-0 w-[80%] h-[80%] bg-cyan-500/10 blur-[80px] rounded-full pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity duration-700" />
        <div className="flex items-center justify-between mb-6 shrink-0 z-10 relative gap-3 flex-wrap">
          <h3 className="text-sm md:text-xl font-bold text-white flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/5 w-fit"><LineChart className="text-cyan-400 w-4 h-4" /> Cumulative Equity</h3>
          {hoverPoint && (
            <div className="flex items-center gap-3 text-[11px] md:text-xs font-bold bg-white/5 border border-cyan-500/30 px-3 py-2 rounded-lg">
              <span className="text-slate-400 uppercase tracking-wider">{hoverPoint.date}</span>
              <span className="text-cyan-400">${hoverPoint.equity.toLocaleString()}</span>
            </div>
          )}
        </div>
        <div className="flex-1 relative z-10 w-full h-full min-h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                </linearGradient>
                <filter id="glowChart"><feGaussianBlur stdDeviation="3" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="rgba(148,163,184,0.6)"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
              />
              <YAxis
                stroke="rgba(148,163,184,0.6)"
                tick={{ fontSize: 10, fill: '#94a3b8' }}
                tickLine={false}
                axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
                domain={[Math.floor(yMin - yPad), Math.ceil(yMax + yPad)]}
                tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
                width={55}
              />
              <RechartsTooltip
                content={<CustomTooltip />}
                cursor={{ stroke: '#06b6d4', strokeWidth: 1, strokeDasharray: '4 4' }}
              />
              {hoverPoint && (
                <ReferenceLine
                  y={hoverPoint.equity}
                  stroke="#06b6d4"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                  ifOverflow="extendDomain"
                />
              )}
              <Area type="monotone" dataKey="equity" stroke="#06b6d4" strokeWidth={3} fillOpacity={1} fill="url(#colorEquity)" activeDot={{ r: 6, fill: '#fff', stroke: '#06b6d4', strokeWidth: 2, className: 'animate-pulse' }} filter="url(#glowChart)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-white/5 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-8 relative overflow-hidden">
        <div className="absolute -top-8 left-1/3 w-44 h-44 bg-lime-500/10 blur-[70px] rounded-full pointer-events-none" />
        <div className="relative z-10 flex items-center justify-between gap-3 flex-wrap mb-5">
          <h3 className="text-sm md:text-xl font-bold text-white flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/5 w-fit">
            <BarChart3 className="text-lime-400 w-4 h-4" />
            Winning Playbook Analyzer V2
          </h3>
          <div className="text-[11px] md:text-xs font-semibold text-slate-400">
            sample={paSampleSize} • sparse={paSparse ? 'yes' : 'no'}
          </div>
        </div>

        {(!playbookAnalysis || paSampleSize <= 0) ? (
          <div className="relative z-10 border border-white/10 rounded-2xl p-4 md:p-6 bg-[#050505]">
            <p className="text-slate-300 text-sm font-semibold">Not enough closed strategy trades yet for playbook analysis.</p>
            <p className="text-slate-500 text-xs mt-2">This section auto-populates when the learning window has usable recent trade history.</p>
          </div>
        ) : (
          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="border border-lime-500/20 rounded-2xl p-4 bg-lime-500/5">
              <p className="text-[11px] uppercase tracking-wider font-bold text-lime-300 mb-2">Best Working Setups</p>
              {(paPromote.slice(0, 3).length > 0) ? (
                <div className="space-y-2">
                  {paPromote.slice(0, 3).map((row, idx) => (
                    <p key={`promote-${idx}`} className="text-[12px] md:text-xs text-slate-200 leading-relaxed">{formatCluster(row)}</p>
                  ))}
                </div>
              ) : (
                <p className="text-[12px] md:text-xs text-slate-400">No promote setups yet. Keep collecting closed trades.</p>
              )}
            </div>

            <div className="border border-rose-500/20 rounded-2xl p-4 bg-rose-500/5">
              <p className="text-[11px] uppercase tracking-wider font-bold text-rose-300 mb-2">Underperforming Setups</p>
              {(paAvoid.slice(0, 3).length > 0) ? (
                <div className="space-y-2">
                  {paAvoid.slice(0, 3).map((row, idx) => (
                    <p key={`avoid-${idx}`} className="text-[12px] md:text-xs text-slate-200 leading-relaxed">{formatCluster(row)}</p>
                  ))}
                </div>
              ) : (
                <p className="text-[12px] md:text-xs text-slate-400">No avoid setups flagged in this sample.</p>
              )}
            </div>

            <div className="border border-cyan-500/20 rounded-2xl p-4 bg-cyan-500/5">
              <p className="text-[11px] uppercase tracking-wider font-bold text-cyan-300 mb-2">Coverage Gaps</p>
              <div className="space-y-2">
                <p className="text-[12px] md:text-xs text-slate-200">Wins with reasoning: <span className="text-cyan-300 font-bold">{paWinsReasonPct.toFixed(1)}%</span></p>
                <p className="text-[12px] md:text-xs text-slate-200">Closed trades with usable tags: <span className="text-cyan-300 font-bold">{paUsableTagsPct.toFixed(1)}%</span></p>
                <p className="text-[12px] md:text-xs text-slate-200">Winning trades weak/missing strong match: <span className="text-cyan-300 font-bold">{paWeakMatchPct.toFixed(1)}%</span></p>
                {paSparse && (
                  <p className="text-[11px] text-amber-300 font-semibold pt-1">Sparse-data mode: treat setup ranking as directional, not definitive.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsTab({ onBotConnected }) {
  const [status, setStatus] = useState('disconnected');
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    apiFetch('/bitunix/status')
      .then(r => r.json())
      .then(d => {
        if (d.linked && d.online) setStatus('synced');
        else if (d.linked && !d.online) setStatus('error');
      })
      .catch(console.error);
  }, []);

  const handleConnect = () => {
    setIsConfiguring(true);
  };

  const handleSave = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await apiFetch('/bitunix/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret })
      });
      if (!resp.ok) {
        const message = await readApiErrorMessage(resp, 'Failed to connect. Make sure your keys only have Trade permission.');
        throw new Error(message);
      }
      const data = await resp.json().catch(() => ({}));
      if (data?.success === false) throw new Error(data.message || data.detail || 'Failed to connect.');
      
      setStatus('synced');
      setIsConfiguring(false);
      setApiKey('');
      setApiSecret('');
      if (onBotConnected) onBotConnected();
    } catch (e) {
      setErrorMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await apiFetch('/bitunix/keys/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret })
      });
      if (!resp.ok) {
        const message = await readApiErrorMessage(resp, 'Test failed.');
        throw new Error(message);
      }
      const data = await resp.json().catch(() => ({}));
      if (data?.success === false) throw new Error(data.message || data.detail || 'Test failed.');
      
      alert('✅ Connection successful! Keys are valid.');
    } catch (e) {
      setErrorMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to decouple this API Bridge? AutoTrade will halt.')) return;
    setLoading(true);
    try {
      await apiFetch('/bitunix/keys', { method: 'DELETE' });
      setStatus('disconnected');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">API Bridges</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Securely link your liquidity providers to CryptoMentor AI.</p></header>
      <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-white/5 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-12 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-orange-500/5 to-transparent pointer-events-none" />
        <div className="relative p-4 md:p-6 bg-orange-500/10 border border-orange-500/20 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="p-2 bg-orange-500/20 rounded-xl shrink-0 border border-orange-500/30 w-fit"><Shield className="text-orange-400 w-6 h-6" /></div>
          <div><h4 className="text-orange-400 font-bold text-xs tracking-wider uppercase mb-1">Security Protocol</h4><p className="text-orange-200/80 font-medium leading-relaxed text-xs">Ensure your API keys have <strong className="text-white">Withdrawals DISABLED</strong>. The AI engine only requires execution and read privileges.</p></div>
        </div>
        
        {isConfiguring ? (
          <div className="p-5 md:p-8 bg-white/5 border border-white/10 rounded-2xl relative z-10 animate-in fade-in">
            <h3 className="text-white font-black text-lg mb-4">Configure Bitunix Network</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">API Key</label>
                <input 
                  type="text" 
                  value={apiKey} 
                  onChange={e => setApiKey(e.target.value)} 
                  className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-mono text-sm" 
                  placeholder="Paste your API Key" 
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">API Secret</label>
                <input 
                  type="password" 
                  value={apiSecret} 
                  onChange={e => setApiSecret(e.target.value)} 
                  className="w-full bg-[#050505] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all font-mono text-sm" 
                  placeholder="Paste your API Secret" 
                />
              </div>
              {errorMsg && <p className="text-rose-400 text-xs font-bold bg-rose-500/10 p-3 rounded-lg border border-rose-500/20">{errorMsg}</p>}
              <div className="flex flex-col sm:flex-row gap-3 pt-4">
                <button 
                  onClick={handleTest} 
                  disabled={loading || !apiKey || !apiSecret}
                  className="flex-1 font-bold px-6 py-3 border rounded-xl transition-all text-sm text-fuchsia-400 border-fuchsia-500/30 bg-fuchsia-500/10 hover:bg-fuchsia-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Testing...' : 'Test Connection'}
                </button>
                <button 
                  onClick={handleSave} 
                  disabled={loading || !apiKey || !apiSecret}
                  className="flex-1 font-bold px-6 py-3 border rounded-xl transition-all text-sm text-cyan-400 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? '...' : 'Save Connectivity'}
                </button>
                <button 
                  onClick={() => setIsConfiguring(false)} 
                  disabled={loading}
                  className="w-full sm:w-auto font-bold px-6 py-3 border rounded-xl transition-all text-sm text-white border-white/10 bg-white/5 hover:bg-white/10"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3 relative z-10 mt-6">
            <BridgeCard 
              name="Bitunix" 
              status={status} 
              logoSrc={bitunixLogo}
              colors="from-blue-500 to-indigo-600" 
              onConnect={handleConnect}
              onDisconnect={handleDisconnect}
              loading={loading}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function SignalsTab({ user, riskSettings, oneClickRiskPct, onUpdateOneClickRisk, focusedSignalId, focusAction }) {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [sortBy, setSortBy] = useState('default'); // 'default' | 'confidence' | 'newest'

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const params = new URLSearchParams();
        if (focusedSignalId) params.set('signal_id', String(focusedSignalId));
        if (focusAction) params.set('action', String(focusAction));
        const endpoint = params.toString() ? `/dashboard/signals?${params.toString()}` : '/dashboard/signals';
        const r = await apiFetch(endpoint);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (cancelled) return;
        setSignals(data.signals || []);
        setUpdatedAt(new Date());
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e.message || 'Failed to load signals');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [focusedSignalId, focusAction]);

  const stamp = updatedAt ? updatedAt.toLocaleTimeString('en-GB', { timeZone: 'Asia/Singapore', hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' UTC+8' : '—';

  const sortedSignals = [...signals].sort((a, b) => {
    const aFocused = (!!focusedSignalId && String(a.signal_id || '') === String(focusedSignalId)) || !!a.focus_match;
    const bFocused = (!!focusedSignalId && String(b.signal_id || '') === String(focusedSignalId)) || !!b.focus_match;
    if (aFocused !== bFocused) return aFocused ? -1 : 1;
    if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0);
    if (sortBy === 'newest') return (Date.parse(b.generated_at || 0)) - (Date.parse(a.generated_at || 0));
    return 0;
  });

  const sortBtns = [
    { key: 'default', label: 'Default' },
    { key: 'confidence', label: 'AI Conf' },
    { key: 'newest', label: 'Latest' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">AI Intelligence Hub</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Real-time market analysis and algorithmic signals. <span className="text-slate-500">Updated {stamp}</span></p></div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {/* Sort buttons */}
          <div className="flex items-center gap-1 bg-white/5 border border-white/10 rounded-xl p-1">
            {sortBtns.map(btn => (
              <button
                key={btn.key}
                onClick={() => setSortBy(btn.key)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-black tracking-widest uppercase transition-all ${
                  sortBy === btn.key
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {btn.label}
              </button>
            ))}
          </div>
          {/* Scanning indicator */}
          <div className="flex items-center gap-2 bg-fuchsia-500/10 border border-fuchsia-500/20 px-4 py-2.5 rounded-xl backdrop-blur-md">
            <div className="relative flex h-2.5 w-2.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fuchsia-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-fuchsia-500"></span></div>
            <span className="text-xs font-bold text-fuchsia-400 tracking-[0.1em] uppercase">{loading ? 'Loading' : 'Scanning Markets'}</span>
          </div>
        </div>
      </header>
      {/* Risk Level Quick Switch */}
      {riskSettings && onUpdateOneClickRisk && (
        <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-white/10 rounded-2xl p-4 md:p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">⚡ 1-Click Risk Level Per Trade</p>
              <div className="flex flex-wrap gap-2">
                {ONE_CLICK_RISK_OPTIONS.map(risk => (
                  <button key={risk} onClick={() => onUpdateOneClickRisk(risk)} disabled={riskSettings?.loading}
                    className={`px-4 py-2 rounded-xl font-bold text-xs transition-all ${
                      getOneClickRiskButtonTone(risk, oneClickRiskPct === risk)
                    } disabled:opacity-50`}>{`${risk}%`}</button>
                ))}
              </div>
            </div>
            {riskSettings?.equity > 0 && (
              <div className="flex items-center gap-4 text-sm">
                <div className="text-right">
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Equity</p>
                  <p className="text-cyan-400 font-bold">${riskSettings.equity.toLocaleString('en-US', {maximumFractionDigits: 2})}</p>
                </div>
                <div className="w-px h-8 bg-white/10" />
                <div className="text-right">
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Target Risk/Trade</p>
                  <p className={`font-bold ${getOneClickRiskValueTone(oneClickRiskPct)}`}>${(riskSettings.equity * (oneClickRiskPct / 100)).toLocaleString('en-US', {maximumFractionDigits: 2})}</p>
                </div>
              </div>
            )}
          </div>
          <p className={`text-[10px] mt-2 ${getOneClickRiskValueTone(oneClickRiskPct)}`}>
            {getOneClickRiskDescription(oneClickRiskPct)}
          </p>
        </div>
      )}

      {error && <div className="text-rose-400 text-sm font-bold bg-rose-500/10 border border-rose-500/20 px-4 py-3 rounded-xl">Failed to load live signals: {error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {sortedSignals.map((signal, idx) => (
          <div
            key={signal.signal_id || signal.id || signal.pair}
            className={`animate-in fade-in slide-in-from-bottom-8 rounded-[1.5rem] ${((focusedSignalId && String(signal.signal_id || '') === String(focusedSignalId)) || signal.focus_match) ? 'ring-2 ring-cyan-400/60 shadow-[0_0_35px_rgba(34,211,238,0.25)]' : ''}`}
            style={{ animationDelay: `${idx * 100}ms`, animationFillMode: 'both' }}
          >
            <SignalCard
              signal={signal}
              userIsPremium={user?.is_premium}
              riskSettings={riskSettings}
              oneClickRiskPct={oneClickRiskPct}
              onUpdateOneClickRisk={onUpdateOneClickRisk}
              isFocused={((focusedSignalId && String(signal.signal_id || '') === String(focusedSignalId)) || !!signal.focus_match)}
              focusAction={((focusedSignalId && String(signal.signal_id || '') === String(focusedSignalId)) || !!signal.focus_match)
                ? (focusAction || signal.focus_action || '')
                : ''}
            />
          </div>
        ))}
        {!loading && !signals.length && !error && <div className="col-span-full text-center text-slate-500 text-sm py-10">No signals available right now.</div>}
      </div>
    </div>
  );
}

function SkillsTab() {
  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">CryptoMentor Academy</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Master risk management, StackMentor execution, and institutional flow.</p></header>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {MOCK_COURSES.map((course, idx) => (
          <div key={course.id} className="animate-in fade-in slide-in-from-bottom-8" style={{ animationDelay: `${idx * 150}ms`, animationFillMode: 'both' }}>
            <CourseCard course={course} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// REFERRAL TAB
// ─────────────────────────────────────────────────────────────────────────────
function ReferralTab({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState('view'); // 'view' | 'form'
  const [form, setForm] = useState({ community_name: '', bitunix_referral_code: '', bitunix_uid: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await apiFetch('/dashboard/referral');
      if (r.ok) setData(await r.json());
    } catch {}
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const copyLink = (link) => {
    navigator.clipboard.writeText(link).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const r = await apiFetch('/dashboard/referral/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setError(d.detail || 'Registration failed'); setSubmitting(false); return; }
      await load();
      setStep('view');
    } catch (e) {
      setError(e.message);
    }
    setSubmitting(false);
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-slate-400 text-sm animate-pulse">Loading referral data...</div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8">
        <h2 className="text-3xl md:text-4xl font-black text-white mb-2 tracking-tighter">Referral Partner</h2>
        <p className="text-slate-400 text-sm md:text-base">Register your community and get an exclusive referral link.</p>
      </header>

      {/* Info card */}
      <div className="bg-gradient-to-br from-fuchsia-500/10 to-cyan-500/10 border border-fuchsia-500/20 rounded-2xl p-5 md:p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-fuchsia-500/15 border border-fuchsia-500/20 shrink-0">
            <Users size={22} className="text-fuchsia-400" />
          </div>
          <div>
            <h3 className="text-white font-bold mb-1">Partner Benefits</h3>
            <ul className="text-slate-300 text-sm space-y-1">
              <li>• Exclusive referral link for your community</li>
              <li>• Track how many members are actively trading</li>
              <li>• Help your community grow trading volume</li>
              <li>• Free — no registration fee</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Status: not registered */}
      {(!data?.registered || step === 'form') && (
        <div className="bg-[#0a0a0a]/80 border border-white/10 rounded-2xl p-6">
          {step === 'view' ? (
            <div className="text-center py-4">
              <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-4">
                <Users size={28} className="text-slate-400" />
              </div>
              <h3 className="text-white font-bold text-lg mb-2">Not Registered</h3>
              <p className="text-slate-400 text-sm mb-6">You haven't registered as a Referral Partner yet. Sign up now — it's free!</p>
              <button
                onClick={() => setStep('form')}
                className="px-6 py-3 bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-500/30 rounded-xl font-bold hover:bg-fuchsia-500/30 transition-all"
              >
                Register Now
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <h3 className="text-white font-bold text-lg mb-4">Register as Referral Partner</h3>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5 block">Community Name</label>
                <input
                  type="text"
                  placeholder="e.g. Crypto Traders, Trading Academy"
                  value={form.community_name}
                  onChange={e => setForm(f => ({ ...f, community_name: e.target.value }))}
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-fuchsia-500/50"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5 block">Bitunix Referral Code</label>
                <input
                  type="text"
                  placeholder="e.g. ABC123 (Bitunix → Profile → Referral Program)"
                  value={form.bitunix_referral_code}
                  onChange={e => setForm(f => ({ ...f, bitunix_referral_code: e.target.value }))}
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-fuchsia-500/50"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5 block">Your Bitunix UID</label>
                <input
                  type="text"
                  placeholder="e.g. 123456789 (Login Bitunix → tap profile photo)"
                  value={form.bitunix_uid}
                  onChange={e => setForm(f => ({ ...f, bitunix_uid: e.target.value }))}
                  required
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-fuchsia-500/50"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                  <AlertCircle size={16} className="text-rose-400 shrink-0" />
                  <p className="text-rose-300 text-sm">{error}</p>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => { setStep('view'); setError(null); }}
                  className="flex-1 py-3 bg-white/5 text-slate-300 border border-white/10 rounded-xl font-bold hover:bg-white/10 transition-all text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 py-3 bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-500/30 rounded-xl font-bold hover:bg-fuchsia-500/30 transition-all text-sm disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Registration'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Status: pending */}
      {data?.registered && data?.status === 'pending' && step === 'view' && (
        <div className="bg-[#0a0a0a]/80 border border-amber-500/20 rounded-2xl p-6 text-center">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
            <Clock size={24} className="text-amber-400" />
          </div>
          <h3 className="text-white font-bold text-lg mb-2">Pending Approval</h3>
          <p className="text-slate-400 text-sm mb-1">Community <span className="text-white font-semibold">{data.community_name}</span> is under admin review.</p>
          <p className="text-slate-500 text-xs">You'll be notified once approved (1–2 business days).</p>
        </div>
      )}

      {/* Status: rejected */}
      {data?.registered && data?.status === 'rejected' && step === 'view' && (
        <div className="bg-[#0a0a0a]/80 border border-rose-500/20 rounded-2xl p-6 text-center">
          <div className="w-14 h-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-4">
            <XCircle size={24} className="text-rose-400" />
          </div>
          <h3 className="text-white font-bold text-lg mb-2">Registration Rejected</h3>
          <p className="text-slate-400 text-sm mb-4">Community <span className="text-white font-semibold">{data.community_name}</span> was not approved.</p>
          <button
            onClick={() => { setForm({ community_name: '', bitunix_referral_code: '', bitunix_uid: '' }); setStep('form'); }}
            className="px-6 py-3 bg-white/5 text-slate-300 border border-white/10 rounded-xl font-bold hover:bg-white/10 transition-all text-sm"
          >
            Re-register
          </button>
        </div>
      )}

      {/* Status: active */}
      {data?.registered && data?.status === 'active' && step === 'view' && (
        <div className="space-y-4">
          {/* Active badge */}
          <div className="bg-[#0a0a0a]/80 border border-lime-500/20 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-lime-500/10 border border-lime-500/20 flex items-center justify-center">
                  <CheckCheck size={20} className="text-lime-400" />
                </div>
                <div>
                  <h3 className="text-white font-bold">{data.community_name}</h3>
                  <span className="text-xs font-bold text-lime-400 bg-lime-500/10 border border-lime-500/20 px-2 py-0.5 rounded-full">ACTIVE</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-black text-white">{data.member_count || 0}</p>
                <p className="text-xs text-slate-400">Members</p>
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-xs text-slate-400 mb-1">Community Code</p>
                <p className="text-white font-mono font-bold text-sm">{data.community_code}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-3">
                <p className="text-xs text-slate-400 mb-1">Bitunix Referral</p>
                <p className="text-white font-mono font-bold text-sm">{data.bitunix_referral_code}</p>
              </div>
            </div>

            {/* Invite link */}
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Community Invite Link</p>
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl p-3">
                <p className="text-cyan-300 text-sm font-mono flex-1 truncate">{data.invite_link}</p>
                <button
                  onClick={() => copyLink(data.invite_link)}
                  className="shrink-0 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  title="Copy link"
                >
                  {copied ? <CheckCheck size={16} className="text-lime-400" /> : <Copy size={16} className="text-slate-400" />}
                </button>
                <a
                  href={data.invite_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <ExternalLink size={16} className="text-slate-400" />
                </a>
              </div>
              <p className="text-xs text-slate-500 mt-2">Share this link with your community members. When they register for autotrade, their UID verification will be sent to you via Telegram.</p>
            </div>
          </div>

          {/* Bitunix referral link */}
          {data.bitunix_referral_url && (
            <div className="bg-[#0a0a0a]/80 border border-white/10 rounded-2xl p-5">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Bitunix Registration Link (for members)</p>
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl p-3">
                <p className="text-slate-300 text-xs font-mono flex-1 truncate">{data.bitunix_referral_url}</p>
                <button
                  onClick={() => copyLink(data.bitunix_referral_url)}
                  className="shrink-0 p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <Copy size={16} className="text-slate-400" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- SUBCOMPONENTS ---
function NavItem({ icon, label, active, onClick, badge, disabled }) {
  return (
    <button onClick={disabled ? undefined : onClick} disabled={disabled} className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 font-bold text-sm relative overflow-hidden group ${disabled ? 'opacity-40 cursor-not-allowed' : active ? 'text-white' : 'text-slate-400 hover:text-white'}`}>
      {active && !disabled && <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent border border-white/10 shadow-[inset_3px_0_0_0_rgba(255,255,255,1)] rounded-xl z-0" />}
      {!active && !disabled && <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl z-0" />}
      <div className="flex items-center gap-3 w-full">
        <div className={`relative z-10 transition-transform duration-300 ${!disabled && 'group-hover:scale-110'} ${active ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`}>{icon}</div>
        <span className="relative z-10 tracking-wide text-left truncate">{label}</span>
      </div>
      {badge && <span className={`relative z-10 text-[8px] font-black tracking-widest px-1.5 py-0.5 rounded border shrink-0 ml-2 ${badge === 'PRO' ? 'text-fuchsia-300 bg-fuchsia-500/20 border-fuchsia-500/30' : badge === 'Soon' ? 'text-amber-300 bg-amber-500/20 border-amber-500/30' : 'text-cyan-300 bg-cyan-500/20 border-cyan-500/30'}`}>{badge}</span>}
    </button>
  );
}

function StatCard({ title, value, subtext, icon, isPositive, glowColor }) {
  const glowStyles = { cyan: 'shadow-[0_0_40px_rgba(6,182,212,0.15)] border-cyan-500/30', lime: 'shadow-[0_0_40px_rgba(163,230,53,0.15)] border-lime-500/30', fuchsia: 'shadow-[0_0_40px_rgba(217,70,239,0.15)] border-fuchsia-500/30' };
  const iconBg = { cyan: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20', lime: 'bg-lime-500/15 text-lime-400 border-lime-500/20', fuchsia: 'bg-fuchsia-500/15 text-fuchsia-400 border-fuchsia-500/20' };
  return (
    <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl p-5 md:p-7 rounded-[1.5rem] md:rounded-[2rem] border border-white/10 ${glowStyles[glowColor]} transition-all duration-500 md:hover:-translate-y-1 flex items-start justify-between relative overflow-hidden group`}>
      <div className={`absolute -right-10 -top-10 w-24 h-24 rounded-full blur-[40px] opacity-20 pointer-events-none group-hover:opacity-40 bg-${glowColor}-500`} />
      <div className="relative z-10">
        <p className="text-slate-400 font-bold text-[10px] uppercase tracking-[0.15em] mb-2">{title}</p>
        <h3 className="text-2xl md:text-4xl font-black text-white mb-2 tracking-tighter">{value}</h3>
        {subtext && <div className={`inline-flex items-center gap-1.5 text-xs font-black px-2.5 py-1 rounded-xl shadow-inner ${isPositive ? 'bg-lime-500/15 text-lime-400 border border-lime-500/20' : 'bg-rose-500/15 text-rose-400 border border-rose-500/20'}`}>{subtext}</div>}
      </div>
      <div className={`p-3 md:p-4 rounded-xl border relative z-10 shadow-lg ${iconBg[glowColor]} shrink-0`}>{icon}</div>
    </div>
  );
}

function MiniStat({ title, value, subtitle, highlight, glow }) {
  const hoverGlow = { cyan: 'md:hover:border-cyan-500/30', rose: 'md:hover:border-rose-500/30', lime: 'md:hover:border-lime-500/30', fuchsia: 'md:hover:border-fuchsia-500/30' };
  return (
    <div className={`bg-[#0a0a0a]/60 backdrop-blur-xl p-4 md:p-6 rounded-[1.25rem] border border-white/5 transition-all duration-300 ${hoverGlow[glow]} group`}>
      <p className="text-slate-400 font-bold text-[10px] uppercase tracking-[0.15em] mb-1.5">{title}</p>
      <h3 className={`text-xl md:text-3xl font-black mb-1.5 tracking-tighter ${highlight}`}>{value}</h3>
      <p className="text-slate-500 text-[10px] font-medium group-hover:text-slate-400 transition-colors">{subtitle}</p>
    </div>
  );
}

function PositionCard({ position, stackMentorActive, isOneClick = false, onCloseOneClickPosition }) {
  // Normalize: API returns "BUY"/"SELL", mock data uses "LONG"/"SHORT"
  const isLong = position.side === 'LONG' || position.side === 'BUY';
  const sideLabel = isLong ? 'LONG' : 'SHORT';
  const [closing, setClosing] = useState(false);
  const [closeError, setCloseError] = useState(null);

  const handleCloseOneClick = async () => {
    if (!isOneClick || closing || !onCloseOneClickPosition) return;
    setCloseError(null);
    setClosing(true);
    try {
      await onCloseOneClickPosition(position);
    } catch (e) {
      setCloseError(e.message || 'Failed to close position');
    } finally {
      setClosing(false);
    }
  };

  return (
    <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-7 flex flex-col transition-all duration-500 md:hover:-translate-y-1 hover:border-white/20 relative overflow-hidden group">
      <div className={`absolute top-0 left-0 w-1.5 h-full ${isLong ? 'bg-gradient-to-b from-lime-400 to-lime-600' : 'bg-gradient-to-b from-rose-400 to-rose-600'}`} />
      <div className="pl-3 relative z-10 flex flex-col h-full">
        <div className="flex flex-col sm:flex-row justify-between items-start mb-5 gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h4 className="text-white font-black text-xl tracking-tight">{position.pair}</h4>
              <span className={`text-[8px] font-black tracking-widest px-1.5 py-0.5 rounded border ${
                isOneClick
                  ? 'text-amber-300 bg-amber-500/15 border-amber-500/30'
                  : 'text-cyan-300 bg-cyan-500/15 border-cyan-500/30'
              }`}>{isOneClick ? '1-CLICK' : 'AUTOTRADE'}</span>
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-black tracking-wider ${isLong ? 'bg-lime-500/10 text-lime-400 border border-lime-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                {isLong ? <TrendingUp size={12} /> : <TrendingDown size={12} />} {sideLabel} • {position.leverage}
              </div>
            </div>
            <p className="text-slate-400 text-xs font-medium">Margin Alloc: <span className="text-white font-bold bg-white/5 px-2 py-0.5 rounded-md border border-white/5">{position.margin}</span></p>
          </div>
          <div className="text-left sm:text-right">
            <p className="text-slate-500 font-bold text-[10px] uppercase tracking-[0.1em] mb-1">Unrealized PnL</p>
            <p className={`text-xl md:text-2xl font-black tracking-tighter ${position.isProfitable ? 'text-lime-400' : 'text-rose-400'}`}>{position.pnl}</p>
            <div className={`inline-block text-[10px] font-bold px-2 py-1 rounded-md ${position.isProfitable ? 'bg-lime-500/10 text-lime-400' : 'bg-rose-500/10 text-rose-400'}`}>{position.pnlPercent}</div>
            {isOneClick && (
              <div className="mt-3">
                <button
                  onClick={handleCloseOneClick}
                  disabled={closing}
                  className="px-3 py-1.5 rounded-lg text-[10px] font-black tracking-wider uppercase text-rose-300 bg-rose-500/15 border border-rose-500/30 hover:bg-rose-500/25 disabled:opacity-50"
                >
                  {closing ? 'Closing...' : 'Close Position'}
                </button>
              </div>
            )}
          </div>
        </div>
        {stackMentorActive && position.tp && (
          <div className="mb-5 bg-white/[0.02] p-3 rounded-xl border border-white/5 overflow-x-auto custom-scrollbar">
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2 flex items-center gap-2"><Layers size={12}/> StackMentor 3-Tier Targets</p>
            <div className="flex gap-2 min-w-[240px]">
              <TPBadge label="TP1" price={position.tp.tp1.price} hit={position.tp.tp1.hit} />
              <TPBadge label="TP2" price={position.tp.tp2.price} hit={position.tp.tp2.hit} />
              <TPBadge label="TP3" price={position.tp.tp3.price} hit={position.tp.tp3.hit} />
            </div>
          </div>
        )}
        <div className="grid grid-cols-2 gap-3 bg-white/[0.02] rounded-xl p-4 border border-white/5 shadow-inner mt-auto">
          <div><p className="text-slate-500 font-bold text-[10px] uppercase tracking-[0.1em] mb-1.5 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-slate-500 shrink-0"/> Entry Price</p><p className="text-white font-bold text-sm">{position.entry}</p></div>
          <div><p className="text-slate-500 font-bold text-[10px] uppercase tracking-[0.1em] mb-1.5 flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shrink-0"/> Mark Price</p><p className="text-white font-bold text-sm">{position.current}</p></div>
        </div>
        {closeError && (
          <p className="mt-2 text-[10px] font-bold text-rose-400">{closeError}</p>
        )}
      </div>
    </div>
  );
}

function TPBadge({ label, price, hit }) {
  return (
    <div className={`flex-1 flex flex-col items-center justify-center p-2 rounded-lg border transition-colors ${hit ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-[#050505] border-white/5 text-slate-500'}`}>
      <span className="text-[9px] font-black tracking-widest uppercase mb-1">{label}</span>
      <span className={`text-[10px] font-bold ${hit ? 'text-white' : 'text-slate-400'}`}>{price}</span>
      {hit && <div className="mt-1 w-full h-[2px] rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />}
    </div>
  );
}

function BridgeCard({ name, status, logo, logoSrc, colors, onConnect, onDisconnect, loading }) {
  const isSynced = status === 'synced';
  return (
    <div className="border border-white/10 rounded-2xl p-4 md:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white/[0.02] hover:bg-white/[0.04] transition-all hover:border-white/20 group">
      <div className="flex items-center gap-4 w-full">
        <div className={`w-12 h-12 md:w-16 md:h-16 bg-gradient-to-br ${colors} rounded-xl flex items-center justify-center font-black text-white text-xl shadow-lg shrink-0 overflow-hidden`}>
          {logoSrc ? (
            <img src={logoSrc} alt={`${name} logo`} className="w-full h-full object-contain p-1.5 bg-black" />
          ) : (
            logo
          )}
        </div>
        <div className="flex-1">
          <h4 className="text-white font-black text-lg mb-1">{name} Network</h4>
          {isSynced ? <div className="flex items-center gap-1.5 bg-lime-500/10 border border-lime-500/20 px-2.5 py-1 rounded-lg w-fit"><CheckCircle2 size={12} className="text-lime-400"/><span className="text-[10px] text-lime-400 font-bold uppercase tracking-wider">Node Synced</span></div> : <div className="flex items-center gap-1.5 bg-slate-800 border border-slate-700 px-2.5 py-1 rounded-lg w-fit"><span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Disconnected</span></div>}
        </div>
      </div>
      <div className="flex gap-2 w-full sm:w-auto">
        <button 
          onClick={onConnect} 
          disabled={loading}
          className={`flex-1 sm:flex-none font-bold px-6 py-3 border rounded-xl transition-all text-sm ${isSynced ? 'text-white border-white/10 bg-white/5 hover:bg-white/10' : 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20'}`}
        >
          {isSynced ? 'Configure' : 'Connect'}
        </button>
        {isSynced && (
          <button 
            onClick={onDisconnect} 
            disabled={loading}
            className="font-bold px-4 py-3 border rounded-xl transition-all text-sm text-rose-400 border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20"
          >
            <X size={18} />
          </button>
        )}
      </div>
    </div>
  );
}

function SignalCard({
  signal,
  userIsPremium,
  riskSettings,
  oneClickRiskPct,
  onUpdateOneClickRisk,
  isFocused = false,
  focusAction = '',
}) {
  const [isPlaced, setIsPlaced] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [instantExecuting, setInstantExecuting] = useState(false);
  const [placeError, setPlaceError] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [confirmError, setConfirmError] = useState(null);
  const [riskAckChecked, setRiskAckChecked] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const [activeRequestId, setActiveRequestId] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const [riskDraft, setRiskDraft] = useState(null);
  const [sliderRisk, setSliderRisk] = useState(null);
  const cardRef = useRef(null);
  const holdStartedAtRef = useRef(null);
  const holdIntervalRef = useRef(null);
  const isLong = signal.direction === 'LONG';
  const isLocked = signal.premium && !userIsPremium;
  const isExpired = !!signal.expired;
  const gateStatus = String(signal.gate_status || 'approved').toLowerCase();
  const gateReasons = Array.isArray(signal.gate_reasons) ? signal.gate_reasons : [];
  const blockedByGate = gateStatus === 'blocked';
  const blockedReason = String(signal.blocked_reason || gateReasons.join('; ') || '').trim();

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const windowMs = (signal.entry_window_seconds || 300) * 1000;
  const generatedMs = signal.generated_at ? Date.parse(signal.generated_at) : now;
  const ageMs = Math.max(0, now - generatedMs);
  const remainingMs = Math.max(0, windowMs - ageMs);
  const windowExpired = remainingMs <= 0;
  const oneClickRisk = normalizeOneClickRisk(oneClickRiskPct || 3.0);
  const controlRiskPct = sliderRisk !== null ? sliderRisk : oneClickRisk;
  const sliderValue = oneClickSliderValueFromRisk(controlRiskPct);
  const requiresRiskAck = controlRiskPct >= 50;
  const requiresHold = controlRiskPct >= 100;
  const userState = String(signal.user_state || 'ready');
  const isUserStateBlocked = ['pending', 'blocked', 'open_1click'].includes(userState);
  const autoExecuteInstant = isFocused && String(focusAction || '').toLowerCase() === 'instant_1click';
  const instantSignalId = String(signal.signal_id || '').trim();
  const instantConsumeKey = instantSignalId ? `cm_instant_exec_state_${instantSignalId}` : '';
  const instantReqKey = instantSignalId ? `cm_instant_exec_req_${instantSignalId}` : '';
  const remainingLabel = windowExpired
    ? 'Entry window closed'
    : `${Math.floor(remainingMs / 60000)}:${String(Math.floor((remainingMs % 60000) / 1000)).padStart(2, '0')} left`;

  const clearHold = () => {
    if (holdIntervalRef.current) {
      clearInterval(holdIntervalRef.current);
      holdIntervalRef.current = null;
    }
    holdStartedAtRef.current = null;
    setHoldProgress(0);
  };

  useEffect(() => {
    return () => clearHold();
  }, []);

  useEffect(() => {
    if (!isFocused || !cardRef.current) return;
    try {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch {}
  }, [isFocused]);

  const closeConfirmModal = () => {
    clearHold();
    setShowConfirm(false);
    setConfirmError(null);
    setRiskAckChecked(false);
  };

  useEffect(() => {
    if (!autoExecuteInstant) return;
    if (!instantSignalId || !signal.signal_token) return;
    if (isLocked || isExpired || blockedByGate || windowExpired || isUserStateBlocked || isPlaced) return;

    let state = '';
    try {
      state = sessionStorage.getItem(instantConsumeKey) || '';
      if (state === 'done' || state === 'failed') return;
    } catch {}

    let cancelled = false;
    const run = async () => {
      setInstantExecuting(true);
      setPlaceError(null);
      try {
        let requestId = '';
        try {
          requestId = sessionStorage.getItem(instantReqKey) || '';
        } catch {}
        if (!requestId) {
          requestId = `instantdl_${makeClientRequestId()}`;
          try { sessionStorage.setItem(instantReqKey, requestId); } catch {}
        }
        try { sessionStorage.setItem(instantConsumeKey, 'started'); } catch {}

        const r = await apiFetch('/dashboard/signals/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            signal_token: signal.signal_token,
            client_request_id: requestId,
          }),
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) {
          throw new Error(mapOneClickReasonMessage(data?.detail || data?.message || `HTTP ${r.status}`));
        }
        if (cancelled) return;
        setIsPlaced(true);
        try { sessionStorage.setItem(instantConsumeKey, 'done'); } catch {}
      } catch (e) {
        if (cancelled) return;
        setPlaceError(e?.message || 'Instant execute failed');
        try { sessionStorage.setItem(instantConsumeKey, 'failed'); } catch {}
      } finally {
        if (!cancelled) setInstantExecuting(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [
    autoExecuteInstant,
    blockedByGate,
    instantConsumeKey,
    instantReqKey,
    instantSignalId,
    isExpired,
    isLocked,
    isPlaced,
    isUserStateBlocked,
    signal.signal_token,
    windowExpired,
  ]);

  const openPreviewModal = async () => {
    if (previewing || confirming || instantExecuting || isPlaced || windowExpired || isUserStateBlocked) return;
    if (!signal.signal_token) {
      setPlaceError('Signal token missing. Please refresh signals.');
      return;
    }
    setPreviewing(true);
    setPlaceError(null);
    setConfirmError(null);
    try {
      const requestId = makeClientRequestId();
      setActiveRequestId(requestId);
      const r = await apiFetch('/dashboard/signals/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_token: signal.signal_token,
          client_request_id: requestId,
          risk_override_pct: controlRiskPct,
          all_in: controlRiskPct >= 100,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        throw new Error(mapOneClickReasonMessage(data?.detail || data?.message || `HTTP ${r.status}`));
      }
      setPreviewData(data);
      if (data?.can_execute?.allowed === false) {
        setConfirmError(mapOneClickReasonMessage(data?.can_execute));
      }
      setShowConfirm(true);
    } catch (e) {
      setPlaceError(e.message || 'Failed to preview order');
    } finally {
      setPreviewing(false);
    }
  };

  const submitExecute = async () => {
    if (confirming || previewing || !previewData) return;
    if (previewData?.can_execute?.allowed === false) {
      setConfirmError(mapOneClickReasonMessage(previewData?.can_execute));
      return;
    }
    if (requiresRiskAck && !riskAckChecked) {
      setConfirmError('Please confirm high-risk acknowledgment before executing.');
      return;
    }
    setConfirming(true);
    setConfirmError(null);
    try {
      const r = await apiFetch('/dashboard/signals/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_token: signal.signal_token,
          client_request_id: activeRequestId || makeClientRequestId(),
          risk_override_pct: controlRiskPct,
          all_in: controlRiskPct >= 100,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) {
        throw new Error(mapOneClickReasonMessage(data?.detail || data?.message || `HTTP ${r.status}`));
      }
      setIsPlaced(true);
      closeConfirmModal();
    } catch (e) {
      setConfirmError(e.message || 'Failed to place order');
    } finally {
      setConfirming(false);
    }
  };

  const beginHoldToConfirm = () => {
    if (!requiresHold || confirming || previewing) return;
    if (previewData?.can_execute?.allowed === false) {
      setConfirmError(mapOneClickReasonMessage(previewData?.can_execute));
      return;
    }
    if (requiresRiskAck && !riskAckChecked) {
      setConfirmError('Please confirm high-risk acknowledgment before executing.');
      return;
    }
    clearHold();
    const startedAt = Date.now();
    holdStartedAtRef.current = startedAt;
    holdIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startedAt;
      const pct = Math.max(0, Math.min(100, (elapsed / 1200) * 100));
      setHoldProgress(pct);
      if (pct >= 100) {
        clearHold();
        submitExecute();
      }
    }, 30);
  };

  const cancelHoldToConfirm = () => {
    if (requiresHold) clearHold();
  };

  const commitRisk = (value) => {
    const normalized = normalizeOneClickRisk(value);
    setSliderRisk(normalized);
    onUpdateOneClickRisk(normalized);
  };

  useEffect(() => {
    if (!riskSettings?.loading) setSliderRisk(null);
  }, [riskSettings?.loading, oneClickRisk]);

  return (
    <div ref={cardRef} className={`bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-6 flex flex-col transition-all duration-500 relative overflow-hidden group hover:border-white/20 ${isLocked ? 'opacity-80' : ''} ${isExpired ? 'opacity-60 grayscale' : ''}`}>
      <div className={`absolute top-0 left-0 w-full h-1 ${isLong ? 'bg-gradient-to-r from-lime-400 to-lime-600' : 'bg-gradient-to-r from-rose-400 to-rose-600'}`} />
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h4 className="text-white font-black text-lg tracking-tight">{signal.pair}</h4>
            {signal.premium ? <span className="text-[8px] font-black tracking-widest text-fuchsia-300 bg-fuchsia-500/20 px-1.5 py-0.5 rounded border border-fuchsia-500/30">PRO</span> : <span className="text-[8px] font-black tracking-widest text-cyan-300 bg-cyan-500/20 px-1.5 py-0.5 rounded border border-cyan-500/30">FREE</span>}
          </div>
          <div className="flex items-center gap-2">
            <span className={`flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-black tracking-wider ${isLong ? 'text-lime-400 bg-lime-500/10' : 'text-rose-400 bg-rose-500/10'}`}>{isLong ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />} {signal.direction}</span>
            <span className="text-[10px] text-slate-400 font-bold bg-white/5 px-2 py-0.5 rounded-md border border-white/5">{signal.type}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center justify-end gap-1 mb-1"><Clock size={12} className="text-slate-500" /><span className="text-xs text-slate-400 font-medium">{signal.time}</span></div>
          <div className="text-[10px] font-bold text-fuchsia-400 bg-fuchsia-500/10 px-2 py-0.5 rounded border border-fuchsia-500/20">{Number(signal.confidence_effective ?? signal.confidence ?? 0).toFixed(1)}% AI CONF</div>
        </div>
      </div>
      {isExpired ? (
        (() => {
          const ts = signal.trade_status;
          const pnl = signal.trade_pnl;
          const pnlStr = typeof pnl === 'number' ? `${pnl >= 0 ? '+' : ''}${pnl.toFixed(2)} USDT` : null;
          if (ts === 'in_position') {
            return (
              <div className="flex-1 flex flex-col items-center justify-center py-6 bg-cyan-500/5 rounded-xl border border-cyan-500/20 mt-2">
                <Zap className="text-cyan-400 w-8 h-8 mb-2" />
                <p className="text-sm font-bold text-white mb-1">In Position</p>
                <p className="text-xs text-slate-400">This symbol already has an active position.</p>
                {pnlStr && <p className={`text-xs font-black mt-2 ${pnl >= 0 ? 'text-lime-400' : 'text-rose-400'}`}>PnL {pnlStr}</p>}
              </div>
            );
          }
          if (ts === 'tp_hit') {
            const hits = signal.tp_hits || {};
            const which = hits.tp3 ? 'TP3' : hits.tp2 ? 'TP2' : hits.tp1 ? 'TP1' : 'TP';
            return (
              <div className="flex-1 flex flex-col items-center justify-center py-6 bg-lime-500/5 rounded-xl border border-lime-500/20 mt-2">
                <CheckCircle2 className="text-lime-400 w-8 h-8 mb-2" />
                <p className="text-sm font-bold text-white mb-1">Take Profit Hit ({which})</p>
                <p className="text-xs text-slate-400">Trade closed in profit.</p>
                {pnlStr && <p className="text-xs font-black mt-2 text-lime-400">PnL {pnlStr}</p>}
              </div>
            );
          }
          if (ts === 'manual_close') {
            return (
              <div className="flex-1 flex flex-col items-center justify-center py-6 bg-amber-500/5 rounded-xl border border-amber-500/20 mt-2">
                <AlertCircle className="text-amber-400 w-8 h-8 mb-2" />
                <p className="text-sm font-bold text-white mb-1">Closed Manually</p>
                <p className="text-xs text-slate-400">The previous 1-click position was closed manually.</p>
              </div>
            );
          }
          // sl_hit / fallback
          return (
            <div className="flex-1 flex flex-col items-center justify-center py-6 bg-rose-500/5 rounded-xl border border-rose-500/20 mt-2">
              <ArrowDownRight className="text-rose-400 w-8 h-8 mb-2" />
              <p className="text-sm font-bold text-white mb-1">Stop Loss Hit</p>
              <p className="text-xs text-slate-400">Trade closed at a loss.</p>
              {pnlStr && <p className="text-xs font-black mt-2 text-rose-400">PnL {pnlStr}</p>}
            </div>
          );
        })()
      ) : isLocked ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 bg-white/[0.02] rounded-xl border border-white/5 mt-2"><Lock className="text-fuchsia-500 w-8 h-8 mb-2 opacity-80" /><p className="text-sm font-bold text-white mb-1">Premium Signal</p><p className="text-xs text-slate-400">Upgrade to access targets.</p></div>
      ) : (
        <div className="flex flex-col gap-3 mt-2">
          <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5"><p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1 flex items-center gap-1.5"><Crosshair size={10} /> Entry Zone</p><p className="text-white font-bold text-sm">{signal.entry}</p></div>
          <div className="flex gap-2">
            <div className="flex-1 bg-white/[0.02] p-3 rounded-xl border border-white/5"><p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Stack Targets</p><div className="flex flex-wrap gap-1">{signal.targets.map((t, i) => <span key={i} className="text-xs font-bold text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">TP{i+1}: {t}</span>)}</div></div>
            <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 min-w-[80px]"><p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Stop Loss</p><p className="text-rose-400 font-bold text-sm">{signal.stopLoss}</p></div>
          </div>
          {signal.user_state && signal.user_state !== 'ready' && (
            <div className="rounded-lg p-2 border border-white/10 bg-white/5 text-[10px] text-slate-300">
              User State: <span className="font-bold uppercase tracking-wider">{String(signal.user_state).replace(/_/g, ' ')}</span>
            </div>
          )}
          {blockedByGate && (
            <div className="rounded-lg p-2 border border-amber-500/30 bg-amber-500/10 text-[10px] text-amber-200">
              Signal blocked by strict gate{blockedReason ? `: ${blockedReason}` : '.'}
            </div>
          )}
          {!isPlaced && !windowExpired && riskSettings?.equity > 0 && signal.stopLoss && (
            <div className={`rounded-lg p-2.5 text-[10px] ${getOneClickRiskPanelTone(controlRiskPct)}`}>
              <div className="flex items-center justify-between">
              <span className="text-slate-500">1-Click will risk:</span>
                <span className={`font-bold ${getOneClickRiskValueTone(controlRiskPct)}`}>
                  ${(riskSettings.equity * (controlRiskPct / 100)).toFixed(2)}
                  <span className="ml-1 text-slate-300/80">({controlRiskPct}% of equity)</span>
                </span>
              </div>
              <p className={`mt-1 text-[10px] font-medium ${getOneClickRiskValueTone(controlRiskPct)}`}>
                {getOneClickRiskDescription(controlRiskPct)}
              </p>
            </div>
          )}
          {!isPlaced && !windowExpired && riskSettings && onUpdateOneClickRisk && (
            <div className="bg-white/5 rounded-lg p-2.5">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-2">Risk Slider (1-Click tiers: 3%, 5%, 10%, 25%, 50%, 100%)</p>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0"
                  max={String(ONE_CLICK_RISK_OPTIONS.length - 1)}
                  step="1"
                  value={sliderValue}
                  disabled={riskSettings?.loading}
                  onChange={e => setSliderRisk(oneClickRiskFromSliderValue(e.target.value))}
                  onMouseUp={e => commitRisk(oneClickRiskFromSliderValue(e.currentTarget.value))}
                  onTouchEnd={e => commitRisk(oneClickRiskFromSliderValue(e.currentTarget.value))}
                  className="flex-1 accent-amber-500 disabled:opacity-40"
                />
                <input
                  type="number"
                  min="3"
                  max="100"
                  step="1"
                  value={riskDraft !== null ? riskDraft : controlRiskPct}
                  disabled={riskSettings?.loading}
                  onChange={e => setRiskDraft(e.target.value)}
                  onBlur={() => {
                    if (riskDraft !== null) {
                      commitRisk(riskDraft);
                      setRiskDraft(null);
                    }
                  }}
                  onKeyDown={e => {
                    if (e.key === 'Enter') e.currentTarget.blur();
                    if (e.key === 'Escape') { setRiskDraft(null); e.target.blur(); }
                  }}
                  className="w-14 px-2 py-1 rounded bg-[#050505] border border-white/10 text-white text-xs font-mono text-center focus:outline-none focus:border-amber-500/50 disabled:opacity-40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
                <span className="text-[10px] text-slate-500 font-bold">%</span>
              </div>
            </div>
          )}
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest mt-1">
            <span className="text-slate-500">Entry Window</span>
            <span className={windowExpired ? 'text-rose-400' : remainingMs < 60000 ? 'text-amber-400' : 'text-cyan-400'}>{remainingLabel}</span>
          </div>
          <button
            onClick={openPreviewModal}
            disabled={isPlaced || previewing || confirming || instantExecuting || windowExpired || isUserStateBlocked || blockedByGate || !signal.signal_token}
            className={`mt-1 w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${isPlaced ? 'bg-lime-500/20 text-lime-400 border border-lime-500/30' : windowExpired ? 'bg-white/5 text-slate-500 border border-white/10' : isLong ? 'bg-lime-500/10 text-lime-400 hover:bg-lime-500/20 border border-lime-500/20' : 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20'}`}
          >
            {isPlaced ? (
              <><CheckCircle2 size={16} /> Position Opened</>
            ) : instantExecuting ? (
              <><Zap size={16} /> Instant Executing…</>
            ) : previewing ? (
              <><Zap size={16} /> Previewing…</>
            ) : windowExpired ? (
              <>Entry Window Closed</>
            ) : blockedByGate ? (
              <>Blocked (strict gate)</>
            ) : isUserStateBlocked ? (
              <>Blocked ({userState.replace(/_/g, ' ')})</>
            ) : (
              <><Zap size={16} /> Review & 1-Click Open {signal.direction}</>
            )}
          </button>
          {placeError && <p className="text-[10px] font-bold text-rose-400 mt-1">{placeError}</p>}
        </div>
      )}
      {showConfirm && (
        <div className="fixed inset-0 z-50 bg-[#020202]/80 backdrop-blur-sm p-4 md:p-5 flex items-center justify-center">
          <div className="w-full max-w-md rounded-2xl border border-white/15 bg-[#090909] p-4 md:p-5">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Pre-Trade Confirmation</p>
                <h5 className="text-white font-black text-lg">{signal.pair} {signal.direction}</h5>
              </div>
              <button type="button" onClick={closeConfirmModal} className="text-slate-400 hover:text-white">
                <X size={16} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] mb-3">
              <div className="rounded-lg border border-white/10 bg-white/5 p-2"><p className="text-slate-500 uppercase text-[9px] tracking-wider">Entry</p><p className="text-white font-bold">{previewData?.sizing?.entry_price || '-'}</p></div>
              <div className="rounded-lg border border-white/10 bg-white/5 p-2"><p className="text-slate-500 uppercase text-[9px] tracking-wider">Leverage</p><p className="text-white font-bold">{previewData?.sizing?.leverage || '-'}x</p></div>
              <div className="rounded-lg border border-white/10 bg-white/5 p-2"><p className="text-slate-500 uppercase text-[9px] tracking-wider">TP</p><p className="text-cyan-300 font-bold">{previewData?.sizing?.tp_price || '-'}</p></div>
              <div className="rounded-lg border border-white/10 bg-white/5 p-2"><p className="text-slate-500 uppercase text-[9px] tracking-wider">SL</p><p className="text-rose-300 font-bold">{previewData?.sizing?.sl_price || '-'}</p></div>
              <div className="rounded-lg border border-white/10 bg-white/5 p-2"><p className="text-slate-500 uppercase text-[9px] tracking-wider">Qty</p><p className="text-white font-bold">{previewData?.sizing?.qty || '-'}</p></div>
              <div className="rounded-lg border border-white/10 bg-white/5 p-2"><p className="text-slate-500 uppercase text-[9px] tracking-wider">Margin</p><p className="text-white font-bold">${Number(previewData?.sizing?.margin_required || 0).toFixed(2)}</p></div>
            </div>

            <div className={`rounded-lg p-2 text-[11px] mb-3 ${getOneClickRiskPanelTone(controlRiskPct)}`}>
              <p className={`font-bold ${getOneClickRiskValueTone(controlRiskPct)}`}>
                Estimated max loss: ${Number(previewData?.sizing?.risk_amount || 0).toFixed(2)}
              </p>
              <p className="text-slate-300">
                Risk {previewData?.sizing?.risk_pct ?? controlRiskPct}% ({previewData?.sizing?.risk_band_label || 'N/A'})
              </p>
              {previewData?.sizing?.cap_applied && (
                <p className="text-amber-300 mt-1">Size capped by balance buffer policy.</p>
              )}
            </div>

            {!!previewData?.warnings?.length && (
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-[11px] text-amber-200 mb-3">
                {previewData.warnings.map((w, idx) => <p key={idx}>{w}</p>)}
              </div>
            )}

            {requiresRiskAck && (
              <label className="flex items-start gap-2 text-[11px] text-slate-300 mb-3">
                <input
                  type="checkbox"
                  checked={riskAckChecked}
                  onChange={(e) => setRiskAckChecked(e.target.checked)}
                  className="mt-0.5 accent-amber-500"
                />
                <span>I understand this is high risk and can cause significant drawdown.</span>
              </label>
            )}

            {confirmError && <p className="text-[11px] font-bold text-rose-400 mb-3">{confirmError}</p>}

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={closeConfirmModal}
                disabled={confirming}
                className="flex-1 py-2.5 rounded-lg border border-white/15 text-slate-300 hover:text-white hover:bg-white/5 disabled:opacity-50"
              >
                Cancel
              </button>
              {!requiresHold ? (
                <button
                  type="button"
                  onClick={submitExecute}
                  disabled={confirming || previewData?.can_execute?.allowed === false}
                  className="flex-1 py-2.5 rounded-lg border border-lime-500/30 bg-lime-500/15 text-lime-300 hover:bg-lime-500/25 disabled:opacity-40 font-bold"
                >
                  {confirming ? 'Placing…' : 'Confirm & Execute'}
                </button>
              ) : (
                <button
                  type="button"
                  onMouseDown={beginHoldToConfirm}
                  onMouseUp={cancelHoldToConfirm}
                  onMouseLeave={cancelHoldToConfirm}
                  onTouchStart={beginHoldToConfirm}
                  onTouchEnd={cancelHoldToConfirm}
                  disabled={confirming || previewData?.can_execute?.allowed === false}
                  className="flex-1 py-2.5 rounded-lg border border-rose-500/30 bg-rose-500/15 text-rose-300 hover:bg-rose-500/25 disabled:opacity-40 font-bold"
                >
                  {confirming ? 'Placing…' : holdProgress > 0 ? `Hold… ${Math.round(holdProgress)}%` : 'Hold 1.2s to Confirm'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function CourseCard({ course }) {
  return (
    <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-7 flex flex-col transition-all duration-500 relative overflow-hidden group ${course.locked ? 'hover:border-white/10' : 'hover:-translate-y-1 hover:border-cyan-500/30 hover:shadow-[0_15px_40px_rgba(6,182,212,0.15)]'}`}>
      {course.locked && <div className="absolute inset-0 bg-[#050505]/60 backdrop-blur-[2px] z-20 flex flex-col items-center justify-center"><div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mb-3 border border-white/10"><Lock className="text-slate-400 w-5 h-5" /></div><span className="text-sm font-bold text-white tracking-wide">PRO Masterclass</span></div>}
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className={`p-3 rounded-xl border shadow-inner ${course.locked ? 'bg-white/5 border-white/10 text-slate-500' : 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'}`}><BookOpen size={20} /></div>
        <span className="text-[10px] font-bold tracking-widest uppercase bg-white/5 px-2 py-1 rounded-md text-slate-400 border border-white/5">{course.category}</span>
      </div>
      <div className="relative z-10 flex-1">
        <h4 className={`font-black text-lg mb-2 tracking-tight ${course.locked ? 'text-slate-300' : 'text-white'}`}>{course.title}</h4>
        <p className="text-xs text-slate-500 font-medium mb-6 flex items-center gap-1.5"><PlayCircle size={12} /> {course.lessons} Video Modules</p>
      </div>
      <div className="mt-auto relative z-10">
        <div className="flex justify-between items-center mb-2"><span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Progress</span><span className={`text-xs font-black ${course.progress === 100 ? 'text-lime-400' : 'text-cyan-400'}`}>{course.progress}%</span></div>
        <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden"><div className={`h-full rounded-full transition-all duration-1000 ${course.progress === 100 ? 'bg-lime-400 shadow-[0_0_10px_rgba(163,230,53,0.8)]' : 'bg-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.8)]'}`} style={{ width: `${course.progress}%` }} /></div>
      </div>
    </div>
  );
}

// ── Verification & Onboarding Screens ────────────────────────────────────────

function GatekeeperScreen({ user, referralUrl, referralSource, referralCode, onSubmitUID, onLogout }) {
  const [step, setStep] = useState(1);
  const [uid, setUID] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState(null);
  const referralResolved = resolveReferralUi(referralUrl, referralSource, referralCode);
  const resolvedReferralUrl = referralResolved.url;
  const resolvedReferralSource = referralResolved.source;

  // After successful submit, show a holding screen — parent will transition to VerificationPendingScreen
  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#020202] p-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] z-0 opacity-50" />
        <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-cyan-600/20 blur-[100px] pointer-events-none z-0" />
        <div className="max-w-lg w-full bg-[#0a0a0a]/60 backdrop-blur-3xl border border-cyan-500/20 rounded-[2rem] p-8 relative z-10 text-center">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={32} className="text-cyan-400" />
          </div>
          <h2 className="text-2xl font-black text-white mb-3">UID Submitted!</h2>
          <p className="text-slate-400 text-sm mb-2">Your Bitunix UID has been sent to our admin for verification.</p>
          <p className="text-slate-500 text-xs mb-8">Please wait — you'll be notified via Telegram once approved. This usually takes a few minutes.</p>
          <div className="flex items-center justify-center gap-2 text-cyan-400 text-sm animate-pulse">
            <div className="w-2 h-2 rounded-full bg-cyan-400" />
            Waiting for admin approval...
          </div>
          <button onClick={onLogout} className="w-full text-slate-500 text-xs mt-8 hover:text-rose-400 transition-colors">Log out</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020202] p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] z-0 opacity-50" />
      <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-fuchsia-600/20 blur-[100px] md:blur-[150px] pointer-events-none animate-pulse z-0" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-cyan-600/20 blur-[100px] md:blur-[150px] pointer-events-none z-0" />
      <div className="max-w-lg w-full bg-[#0a0a0a]/60 backdrop-blur-3xl border border-white/10 rounded-[2rem] p-8 relative z-10">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-[1.25rem] bg-gradient-to-tr from-fuchsia-500 via-purple-500 to-cyan-500 p-[1px] shadow-[0_0_20px_rgba(217,70,239,0.3)]">
            <div className="w-full h-full bg-[#050505] rounded-[19px] flex items-center justify-center"><Bot size={28} className="text-white" /></div>
          </div>
          <div>
            <h1 className="text-2xl font-black text-white">Welcome to CryptoMentor</h1>
            <p className="text-cyan-400 text-xs font-bold tracking-[0.2em] uppercase">Exchange Registration</p>
          </div>
        </div>

        {/* Progress */}
        <div className="flex gap-2 mb-8">
          <div className={`h-1 flex-1 rounded ${step >= 1 ? 'bg-cyan-500' : 'bg-white/10'}`} />
          <div className={`h-1 flex-1 rounded ${step >= 2 ? 'bg-cyan-500' : 'bg-white/10'}`} />
        </div>

        {step === 1 && (
          <>
            <h2 className="text-xl font-bold text-white mb-2">Step 1: Register on Bitunix</h2>
            <p className="text-slate-300 text-sm mb-4">Create a Bitunix account using our referral link. This is required to enable AI-powered trading.</p>
            <a href={resolvedReferralUrl} target="_blank" rel="noopener noreferrer"
              className="block w-full text-center bg-cyan-500 text-white font-bold py-3 rounded-xl mb-4 hover:bg-cyan-600 transition-colors">
              Open Bitunix Registration
            </a>
            <p className="text-xs text-slate-500 mb-3">
              Referral Source: <code className="text-cyan-400">{resolvedReferralSource}</code>
            </p>
            <p className="text-xs text-slate-500 mb-6">
              Community Code: <code className="text-cyan-400">{referralCode || 'none'}</code> (auto-applied via link)
            </p>
            <button onClick={() => setStep(2)} className="w-full bg-white/10 text-white font-bold py-3 rounded-xl hover:bg-white/20 transition-colors">
              I've Already Registered &rarr; Continue
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <h2 className="text-xl font-bold text-white mb-2">Step 2: Submit Your Bitunix UID</h2>
            <p className="text-slate-300 text-sm mb-2">Find your UID: Login to Bitunix &rarr; tap your profile photo &rarr; UID is shown below your name.</p>
            <input type="text" value={uid} onChange={e => setUID(e.target.value)} placeholder="Enter your Bitunix UID (e.g. 123456789)"
              className="w-full bg-white/5 border border-white/20 rounded-xl px-4 py-3 text-white mb-4 mt-2 font-mono focus:border-cyan-500/50 focus:outline-none transition-colors" />
            {error && <p className="text-rose-400 text-sm mb-4 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">{error}</p>}
            <button onClick={async () => {
              setSubmitting(true); setError(null);
              const result = await onSubmitUID(uid);
              setSubmitting(false);
              if (result.ok) {
                setSubmitted(true); // show holding screen — no bypass possible
              } else {
                setError(result.error);
              }
            }} disabled={!uid || uid.length < 5 || submitting}
              className="w-full bg-cyan-500 text-white font-bold py-3 rounded-xl hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              {submitting ? 'Submitting...' : 'Submit for Verification'}
            </button>
            <button onClick={() => setStep(1)} className="w-full text-slate-400 text-sm mt-3 hover:text-white transition-colors">&larr; Back to registration</button>
          </>
        )}

        <button onClick={onLogout} className="w-full text-slate-500 text-xs mt-6 hover:text-rose-400 transition-colors">Log out</button>
      </div>
    </div>
  );
}

function VerificationPendingScreen({ onRefresh, onLogout }) {
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    const interval = setInterval(onRefresh, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020202] p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] z-0 opacity-50" />
      <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-fuchsia-600/20 blur-[100px] md:blur-[150px] pointer-events-none animate-pulse z-0" />
      <div className="max-w-lg w-full bg-[#0a0a0a]/60 backdrop-blur-3xl border border-white/10 rounded-[2rem] p-8 text-center relative z-10">
        <div className="text-6xl mb-6">&#9203;</div>
        <h1 className="text-2xl font-black text-white mb-4">Verification Pending</h1>
        <p className="text-slate-300 mb-2">Your Bitunix UID is being verified by an admin.</p>
        <p className="text-slate-400 text-sm mb-8">You'll receive a Telegram notification once approved. This usually takes a few minutes.</p>
        <button onClick={async () => { setPolling(true); await onRefresh(); setPolling(false); }}
          className="bg-white/10 text-white font-bold px-6 py-3 rounded-xl hover:bg-white/20 transition-colors">
          {polling ? 'Checking...' : 'Refresh Status'}
        </button>
        <button onClick={onLogout} className="block mx-auto text-slate-500 text-xs mt-6 hover:text-rose-400 transition-colors">Log out</button>
      </div>
    </div>
  );
}

function RejectedScreen({ referralUrl, referralSource, referralCode, onResubmit, onLogout }) {
  const [uid, setUid] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const referralResolved = resolveReferralUi(referralUrl, referralSource, referralCode);
  const resolvedReferralUrl = referralResolved.url;
  const resolvedReferralSource = referralResolved.source;

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020202] p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] z-0 opacity-50" />
      <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-rose-600/15 blur-[100px] pointer-events-none z-0" />
      <div className="max-w-lg w-full bg-[#0a0a0a]/60 backdrop-blur-3xl border border-rose-500/20 rounded-[2rem] p-8 relative z-10">
        <div className="text-center mb-6">
          <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-4">
            <XCircle size={32} className="text-rose-400" />
          </div>
          <h2 className="text-2xl font-black text-white mb-2">UID Verification Rejected</h2>
          <p className="text-slate-400 text-sm">Your Bitunix UID was not found under our referral code.</p>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-6 text-sm text-amber-200/80">
          Make sure you registered on Bitunix using our referral link before submitting your UID.
        </div>
        <a href={resolvedReferralUrl} target="_blank" rel="noopener noreferrer"
          className="block w-full text-center bg-fuchsia-500/15 border border-fuchsia-500/30 text-fuchsia-400 font-bold py-3 rounded-xl mb-6 hover:bg-fuchsia-500/25 transition-colors">
          Re-register on Bitunix with Referral →
        </a>
        <p className="text-xs text-slate-500 mb-3">
          Referral Source: <code className="text-cyan-400">{resolvedReferralSource}</code>
        </p>
        <p className="text-xs text-slate-500 mb-6">
          Community Code: <code className="text-cyan-400">{referralCode || 'none'}</code>
        </p>
        <label className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2 block">Submit New UID</label>
        <input type="text" value={uid} onChange={e => setUid(e.target.value)} placeholder="Enter your Bitunix UID"
          className="w-full bg-white/5 border border-white/20 rounded-xl px-4 py-3 text-white mb-3 font-mono focus:border-cyan-500/50 focus:outline-none" />
        {error && <p className="text-rose-400 text-sm mb-3 bg-rose-500/10 border border-rose-500/20 px-3 py-2 rounded-lg">{error}</p>}
        <button onClick={async () => {
          setSubmitting(true); setError(null);
          const result = await onResubmit(uid);
          setSubmitting(false);
          if (!result.ok) setError(result.error);
        }} disabled={!uid || uid.length < 5 || submitting}
          className="w-full bg-cyan-500 text-white font-bold py-3 rounded-xl hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {submitting ? 'Submitting...' : 'Resubmit for Verification'}
        </button>
        <button onClick={onLogout} className="w-full text-slate-500 text-xs mt-6 hover:text-rose-400 transition-colors">Log out</button>
      </div>
    </div>
  );
}

function OnboardingWizard({ onComplete, onLogout }) {
  const [step, setStep] = useState(1);
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testError, setTestError] = useState('');
  const [saving, setSaving] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [riskPerTrade, setRiskPerTrade] = useState(3);
  const [onboardingRiskMin, setOnboardingRiskMin] = useState(0.25);
  const [marginMode, setMarginMode] = useState('cross');
  const [starting, setStarting] = useState(false);
  const [riskConfigError, setRiskConfigError] = useState('');

  useEffect(() => {
    if (step !== 2) return;
    let cancelled = false;
    (async () => {
      try {
        const resp = await apiFetch('/dashboard/settings');
        const data = await resp.json().catch(() => ({}));
        if (cancelled || !resp.ok) return;
        const minFromPolicy = Number(data?.risk_policy?.min_pct);
        const computedFloor = getAutoRiskFloorByEquity(data?.equity);
        const minFloor = Number.isFinite(minFromPolicy) ? Math.max(0.25, minFromPolicy) : computedFloor;
        setOnboardingRiskMin(minFloor);
        setRiskPerTrade((prev) => Math.max(minFloor, normalizeAutoRisk(prev)));
      } catch (e) {
        console.warn('Failed to load onboarding risk floor:', e);
      }
    })();
    return () => { cancelled = true; };
  }, [step]);

  const handleTestConnection = async () => {
    setTestResult(null);
    setTestError('');
    try {
      const resp = await apiFetch('/bitunix/keys/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret }),
      });
      if (!resp.ok) {
        const message = await readApiErrorMessage(resp, 'Connection failed');
        setTestResult('error');
        setTestError(message);
        return;
      }
      const data = await resp.json().catch(() => ({}));
      if (data?.success === false) {
        setTestResult('error');
        setTestError(data.message || data.detail || 'Connection failed');
        return;
      }
      setTestResult('success');
    } catch {
      setTestResult('error');
      setTestError('Network error');
    }
  };

  const handleSaveKeys = async () => {
    setSaving(true);
    setTestError('');
    try {
      const resp = await apiFetch('/bitunix/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret }),
      });
      if (!resp.ok) {
        const message = await readApiErrorMessage(resp, 'Failed to save keys');
        setTestResult('error');
        setTestError(message);
        return;
      }
      const data = await resp.json().catch(() => ({}));
      if (data?.success === false) {
        setTestResult('error');
        setTestError(data.message || data.detail || 'Failed to save keys');
        return;
      }
      setStep(2);
    } catch (e) { setTestResult('error'); setTestError(e.message); }
    finally { setSaving(false); }
  };

  const handleSaveRisk = async () => {
    setRiskConfigError('');
    const effectiveRisk = Math.max(onboardingRiskMin, normalizeAutoRisk(riskPerTrade));
    setRiskPerTrade(effectiveRisk);
    const [riskResp, marginResp] = await Promise.all([
      apiFetch('/dashboard/settings/risk', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ risk_per_trade: effectiveRisk }) }),
      apiFetch('/dashboard/settings/margin-mode', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ margin_mode: marginMode }) }),
    ]);

    if (!riskResp.ok) {
      const err = await riskResp.json().catch(() => ({}));
      setRiskConfigError(err.detail || 'Failed to save risk setting.');
      return;
    }
    if (!marginResp.ok) {
      const err = await marginResp.json().catch(() => ({}));
      setRiskConfigError(err.detail || 'Failed to save margin mode.');
      return;
    }
    setStep(3);
  };

  const handleStartEngine = async () => {
    setStarting(true);
    try { await apiFetch('/dashboard/engine/start', { method: 'POST' }); } catch {}
    setStarting(false);
    onComplete();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020202] p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:40px_40px] z-0 opacity-50" />
      <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-fuchsia-600/20 blur-[100px] md:blur-[150px] pointer-events-none animate-pulse z-0" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[80vw] h-[80vw] md:w-[50vw] md:h-[50vw] rounded-full bg-cyan-600/20 blur-[100px] md:blur-[150px] pointer-events-none z-0" />
      <div className="max-w-lg w-full bg-[#0a0a0a]/60 backdrop-blur-3xl border border-white/10 rounded-[2rem] p-8 relative z-10">
        {/* Progress */}
        <div className="flex gap-2 mb-2">
          {[1, 2, 3].map(s => (
            <div key={s} className={`h-1 flex-1 rounded transition-all ${step >= s ? 'bg-cyan-500' : 'bg-white/10'}`} />
          ))}
        </div>
        <p className="text-xs text-slate-500 mb-6">Step {step}/3</p>

        {step === 1 && (
          <>
            <h2 className="text-xl font-bold text-white mb-2">Connect Your Bitunix API Key</h2>
            <p className="text-slate-400 text-sm mb-6">Link your Bitunix account to enable AI-powered trading.</p>
            <label className="text-xs text-slate-500 font-bold uppercase tracking-wider">API Key</label>
            <input type="text" value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="Enter your Bitunix API Key"
              className="w-full bg-white/5 border border-white/20 rounded-xl px-4 py-3 text-white mb-4 mt-1 font-mono text-sm focus:border-cyan-500/50 focus:outline-none" />
            <label className="text-xs text-slate-500 font-bold uppercase tracking-wider">API Secret</label>
            <input type="password" value={apiSecret} onChange={e => setApiSecret(e.target.value)} placeholder="Enter your Bitunix API Secret"
              className="w-full bg-white/5 border border-white/20 rounded-xl px-4 py-3 text-white mb-4 mt-1 font-mono text-sm focus:border-cyan-500/50 focus:outline-none" />
            <button onClick={() => setShowGuide(!showGuide)} className="text-cyan-400 text-sm mb-4 hover:underline">
              {showGuide ? '\u25BC' : '\u25B6'} How to create your API Key
            </button>
            {showGuide && (
              <div className="bg-white/5 rounded-xl p-4 mb-4 text-sm text-slate-300">
                <ol className="list-decimal list-inside space-y-2">
                  <li><b>Label:</b> <code className="text-cyan-400">CryptoMentor Bot</code> (or any name)</li>
                  <li><b>IP Address:</b> Leave BLANK</li>
                  <li><b>Permissions:</b> Enable <b>Trade</b> only. Do NOT enable Withdraw or Transfer</li>
                  <li>Click <b>Confirm</b> &rarr; verify via email/2FA</li>
                  <li>Copy the <b>API Key</b> and <b>Secret Key</b></li>
                </ol>
                <a href="https://www.bitunix.com/account/api-management" target="_blank" rel="noopener noreferrer"
                  className="inline-block mt-3 text-cyan-400 hover:underline">Open Bitunix API Management &rarr;</a>
              </div>
            )}
            {testResult === 'success' && (
              <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-3 mb-4 text-green-400 text-sm">Connection successful! Your API key is valid.</div>
            )}
            {testResult === 'error' && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 mb-4 text-rose-400 text-sm">{testError || 'Connection failed. Check your API key and secret.'}</div>
            )}
            <div className="flex gap-3">
              <button onClick={handleTestConnection} disabled={!apiKey || !apiSecret}
                className="flex-1 bg-white/10 text-white font-bold py-3 rounded-xl hover:bg-white/20 disabled:opacity-50 transition-colors">
                Test Connection
              </button>
              <button onClick={handleSaveKeys} disabled={!apiKey || !apiSecret || saving}
                className="flex-1 bg-cyan-500 text-white font-bold py-3 rounded-xl hover:bg-cyan-600 disabled:opacity-50 transition-colors">
                {saving ? 'Saving...' : 'Save & Continue'}
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h2 className="text-xl font-bold text-white mb-2">Configure Risk Management</h2>
            <p className="text-slate-400 text-sm mb-6">Set your trading preferences. You can change these anytime from the Engine tab.</p>
            <label className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2 block">Risk Per Trade</label>
            <div className="grid grid-cols-4 gap-2 mb-2">
              {RISK_OPTIONS.map(risk => (
                <button key={risk} onClick={() => setRiskPerTrade(Math.max(risk, onboardingRiskMin))}
                  disabled={risk < onboardingRiskMin}
                  className={`flex-1 py-3 rounded-xl font-bold text-sm transition-all ${
                    riskPerTrade === Math.max(risk, onboardingRiskMin)
                      ? getRiskButtonTone(risk)
                    : risk > 5.0
                        ? 'bg-[#090505] text-amber-300/70 border border-amber-500/15 hover:border-rose-500/35 hover:text-amber-200'
                        : 'bg-white/5 text-green-300/80 border border-green-500/15 hover:border-green-500/35 hover:text-green-200'
                  } disabled:opacity-40`}>{risk}%</button>
              ))}
            </div>
            {onboardingRiskMin > 0.25 && (
              <p className="text-xs mb-2 text-amber-300 font-medium">
                Low equity safeguard active: minimum risk is {onboardingRiskMin}%.
              </p>
            )}
            <p className={`text-xs mb-6 ${riskPerTrade > 5.0 ? 'text-amber-300' : 'text-green-400'}`}>
              {getRiskDescription(riskPerTrade)}
            </p>
            {riskConfigError && (
              <p className="text-xs mb-4 text-rose-400 font-medium">{riskConfigError}</p>
            )}
            <label className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2 block">Leverage</label>
            <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 mb-6">
              <p className="text-sm font-bold text-amber-300">Auto Max Pair Leverage</p>
              <p className="text-xs text-slate-400 mt-1">Calculated by backend from the pair's max allowed leverage.</p>
            </div>
            <label className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2 block">Margin Mode</label>
            <div className="flex gap-2 mb-8">
              <button onClick={() => setMarginMode('cross')}
                className={`flex-1 py-3 rounded-xl font-bold text-sm ${marginMode === 'cross' ? 'bg-cyan-500 text-white' : 'bg-white/5 text-slate-400'}`}>
                Cross
              </button>
              <button onClick={() => setMarginMode('isolated')}
                className={`flex-1 py-3 rounded-xl font-bold text-sm ${marginMode === 'isolated' ? 'bg-cyan-500 text-white' : 'bg-white/5 text-slate-400'}`}>
                Isolated
              </button>
            </div>
            <button onClick={handleSaveRisk} className="w-full bg-cyan-500 text-white font-bold py-3 rounded-xl hover:bg-cyan-600 transition-colors">
              Continue
            </button>
          </>
        )}

        {step === 3 && (
          <>
            <h2 className="text-xl font-bold text-white mb-2">Ready to Trade!</h2>
            <p className="text-slate-400 text-sm mb-6">Review your settings and start the AutoTrade engine.</p>
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-6 space-y-3">
              <div className="flex justify-between"><span className="text-slate-400">Exchange</span><span className="text-white font-bold">Bitunix</span></div>
              <div className="flex justify-between"><span className="text-slate-400">API Key</span><span className="text-white font-mono">...{apiKey.slice(-4)}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Risk Per Trade</span><span className="text-white font-bold">{riskPerTrade}%</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Leverage</span><span className="text-white font-bold">Auto Max Pair</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Margin Mode</span><span className="text-white font-bold">{marginMode === 'cross' ? 'Cross' : 'Isolated'}</span></div>
            </div>
            <button onClick={handleStartEngine} disabled={starting}
              className="w-full bg-lime-500 text-black font-black py-4 rounded-xl text-lg hover:bg-lime-400 disabled:opacity-50 transition-colors mb-3">
              {starting ? 'Starting...' : 'Start AutoTrade Engine'}
            </button>
            <button onClick={() => onComplete()} className="w-full text-slate-400 text-sm hover:text-white py-2 transition-colors">
              Skip for now &rarr; Go to Dashboard
            </button>
          </>
        )}

        <button onClick={onLogout} className="w-full text-slate-500 text-xs mt-6 hover:text-rose-400 transition-colors">Log out</button>
      </div>
    </div>
  );
}

// ── Sidebar Social Proof Ticker ───────────────────────────────────────────────
function SidebarTicker() {
  const [items, setItems] = useState(TICKER_FALLBACK);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/leaderboard/ticker');
        if (!r.ok) return;
        const d = await r.json();
        if (d.items && d.items.length > 0) setItems(d.items);
      } catch {}
    };
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  // Triple-duplicate for seamless vertical loop
  const display = [...items, ...items, ...items];
  const duration = display.length * 2.8;

  return (
    <div className="mx-3 my-2 rounded-2xl overflow-hidden relative border border-white/5 bg-white/[0.02]" style={{ height: '110px' }}>
      {/* header label */}
      <div className="absolute top-0 left-0 right-0 flex items-center gap-1.5 px-3 pt-2 pb-1 z-20"
        style={{ background: 'linear-gradient(180deg, rgba(10,10,10,0.95) 60%, transparent)' }}>
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-lime-400 animate-pulse shrink-0" />
        <span className="text-[9px] font-black tracking-widest uppercase text-lime-400">Live Profits</span>
      </div>

      {/* bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-6 z-20 pointer-events-none"
        style={{ background: 'linear-gradient(0deg, rgba(10,10,10,0.9) 0%, transparent 100%)' }} />

      {/* scrolling rows */}
      <div
        className="flex flex-col pt-6"
        style={{
          animation: `sidebar-ticker-v ${duration}s linear infinite`,
          willChange: 'transform',
        }}
      >
        {display.map((item, i) => (
          <div key={i} className="flex items-center gap-2 px-3 py-[5px] shrink-0">
            <span className="text-lime-400 text-[11px] shrink-0">🔔</span>
            <div className="flex-1 min-w-0">
              <span className="text-white text-[11px] font-bold">{item.user}</span>
              <span className="text-slate-400 text-[11px]"> closed </span>
              <span className="text-cyan-300 text-[11px] font-bold">{(item.symbol || '').replace('USDT', '')}</span>
            </div>
            <span className="text-lime-400 text-[11px] font-black shrink-0">+${Number(item.pnl_usdt).toFixed(2)}</span>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes sidebar-ticker-v {
          0%   { transform: translateY(0); }
          100% { transform: translateY(calc(-100% / 3)); }
        }
      `}</style>
    </div>
  );
}

// ── Profit Ticker Banner ──────────────────────────────────────────────────────
const TICKER_FALLBACK = [
  { user: "al***na", symbol: "BTCUSDT",  pnl_usdt: 84.20,  pnl_pct: 18.4 },
  { user: "ry***to", symbol: "ETHUSDT",  pnl_usdt: 47.55,  pnl_pct: 23.3 },
  { user: "ha***an", symbol: "BTCUSDT",  pnl_usdt: 112.60, pnl_pct: 27.6 },
  { user: "ba***us", symbol: "ETHUSDT",  pnl_usdt: 66.30,  pnl_pct: 31.2 },
  { user: "wi***to", symbol: "BTCUSDT",  pnl_usdt: 95.40,  pnl_pct: 22.8 },
  { user: "yu***ta", symbol: "BTCUSDT",  pnl_usdt: 143.20, pnl_pct: 34.5 },
  { user: "ir***an", symbol: "AVAXUSDT", pnl_usdt: 39.10,  pnl_pct: 19.1 },
  { user: "si***ah", symbol: "ETHUSDT",  pnl_usdt: 52.90,  pnl_pct: 25.7 },
  { user: "fa***ul", symbol: "SOLUSDT",  pnl_usdt: 31.80,  pnl_pct: 14.7 },
  { user: "pr***to", symbol: "BNBUSDT",  pnl_usdt: 33.60,  pnl_pct: 16.2 },
];

function TickerWrapper() {
  const [visible, setVisible] = useState(true);
  const lastY = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      // Only auto-hide on mobile (< 768px)
      if (window.innerWidth >= 768) { setVisible(true); return; }
      if (y > lastY.current && y > 40) {
        setVisible(false); // scrolling down
      } else {
        setVisible(true);  // scrolling up
      }
      lastY.current = y;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className={`sticky top-0 z-50 transition-transform duration-300 ${visible ? 'translate-y-0' : '-translate-y-full'}`}>
      <ProfitTicker />
    </div>
  );
}

function ProfitTicker() {
  const [items, setItems] = useState(TICKER_FALLBACK);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch('/leaderboard/ticker');
        if (!r.ok) return;
        const d = await r.json();
        if (d.items && d.items.length > 0) setItems(d.items);
      } catch {}
    };
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  // Triple-duplicate for seamless infinite loop
  const display = [...items, ...items, ...items];
  const duration = display.length * 3.2;

  return (
    <div
      className="w-full overflow-hidden relative flex items-center shrink-0"
      style={{
        height: '34px',
        background: 'linear-gradient(90deg, #050a05 0%, #071207 50%, #050a05 100%)',
        borderBottom: '1px solid rgba(132,204,22,0.2)',
        zIndex: 60,
      }}
    >
      {/* LIVE label */}
      <div
        className="absolute left-0 top-0 h-full flex items-center gap-1.5 px-3 z-20 shrink-0"
        style={{ background: 'linear-gradient(90deg, #050a05 65%, transparent)' }}
      >
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-lime-400 animate-pulse" />
        <span className="text-[9px] font-black tracking-widest uppercase text-lime-400">LIVE</span>
      </div>

      {/* left fade */}
      <div className="absolute left-16 top-0 h-full w-8 z-10 pointer-events-none"
        style={{ background: 'linear-gradient(90deg, #050a05, transparent)' }} />
      {/* right fade */}
      <div className="absolute right-0 top-0 h-full w-12 z-10 pointer-events-none"
        style={{ background: 'linear-gradient(270deg, #050a05, transparent)' }} />

      <div
        className="flex items-center pl-20"
        style={{
          animation: `ticker-h ${duration}s linear infinite`,
          whiteSpace: 'nowrap',
          willChange: 'transform',
        }}
      >
        {display.map((item, i) => (
          <span key={i} className="inline-flex items-center gap-1.5 px-4 text-[11px]">
            <span className="text-lime-400 text-[10px]">🔔</span>
            <span className="text-slate-400">
              <span className="text-white font-bold">{item.user}</span>
              {' '}closed{' '}
              <span className="text-cyan-300 font-bold">{(item.symbol || '').replace('USDT', '/USDT')}</span>
              {' '}for{' '}
              <span className="text-lime-400 font-black">+${Number(item.pnl_usdt).toFixed(2)}</span>
              {item.pnl_pct > 0 && (
                <span className="text-lime-300/50 text-[10px]"> ({Number(item.pnl_pct).toFixed(1)}%)</span>
              )}
            </span>
            <span className="text-white/10 px-3">·</span>
          </span>
        ))}
      </div>

      <style>{`
        @keyframes ticker-h {
          0%   { transform: translateX(0); }
          100% { transform: translateX(calc(-100% / 3)); }
        }
      `}</style>
    </div>
  );
}

function BotStartModal({ onStart, onCancel }) {  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-md" onClick={onCancel} />

      {/* Modal */}
      <div className="relative z-10 w-full max-w-md bg-[#0a0a0a]/95 border border-white/10 rounded-[2rem] p-8 shadow-[0_0_80px_rgba(0,0,0,0.8)] animate-in fade-in zoom-in-95 duration-300">
        <div className="absolute inset-0 bg-gradient-to-b from-lime-500/5 to-transparent rounded-[2rem] pointer-events-none" />

        {/* Icon */}
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-lime-500/10 border border-lime-500/20 flex items-center justify-center shadow-[0_0_30px_rgba(163,230,53,0.15)]">
          <Power className="w-8 h-8 text-lime-400" />
        </div>

        <h2 className="text-2xl font-black text-white text-center mb-2 tracking-tight">API Connected!</h2>
        <p className="text-slate-400 text-sm text-center font-medium leading-relaxed mb-2">
          Your Bitunix API keys have been saved successfully.
        </p>
        <p className="text-slate-300 text-sm text-center font-semibold mb-8">
          Would you like to <span className="text-lime-400">start the AutoTrade engine</span> now?
        </p>

        {/* Warning */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-6 flex items-start gap-3">
          <Shield className="text-amber-400 w-4 h-4 shrink-0 mt-0.5" />
          <p className="text-amber-200/80 text-xs font-medium leading-relaxed">
            The bot will begin scanning markets and placing trades automatically based on your configured risk settings.
          </p>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-3.5 px-6 rounded-xl font-bold text-sm text-slate-400 border border-white/10 bg-white/5 hover:bg-white/10 transition-all"
          >
            Cancel — Start Later
          </button>
          <button
            onClick={onStart}
            className="flex-1 py-3.5 px-6 rounded-xl font-black text-sm text-lime-400 border border-lime-500/30 bg-lime-500/10 hover:bg-lime-500/20 hover:shadow-[0_0_30px_rgba(163,230,53,0.2)] transition-all flex items-center justify-center gap-2"
          >
            <Power size={16} /> Start Bot Now
          </button>
        </div>
      </div>
    </div>
  );
}

