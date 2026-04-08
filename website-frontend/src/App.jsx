import React, { useState, useEffect } from 'react';
import {
  LineChart, Wallet, Bot, Settings, LogOut,
  TrendingUp, TrendingDown, Activity, CheckCircle2,
  Shield, BarChart2, Target, Zap, Layers, RefreshCw,
  GraduationCap, Radio, Cpu, ToggleRight, ToggleLeft,
  Menu, X, Crosshair, ArrowUpRight, ArrowDownRight,
  PlayCircle, BookOpen, Lock, Clock, Power, StopCircle
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';

const _CONFIGURED_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
const _FALLBACK_BASE = '/api';

// Tracks which base URL is confirmed working so we don't retry every call.
// null = untested, string = confirmed working base.
let _resolvedBase = null;

const apiFetch = async (path, opts = {}) => {
  const token = localStorage.getItem('cm_token');
  const headers = {
    ...(opts.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  // If we already confirmed a working base, use it directly.
  if (_resolvedBase) {
    return fetch(`${_resolvedBase}${path}`, { ...opts, headers });
  }

  // Try the configured base first.
  try {
    const r = await fetch(`${_CONFIGURED_BASE}${path}`, { ...opts, headers });
    _resolvedBase = _CONFIGURED_BASE; // mark as working
    if (r.status === 401) console.warn('[apiFetch] 401 on:', path);
    return r;
  } catch (_networkErr) {
    // Configured base is unreachable (wrong domain, CORS block, etc.).
    // Fall back to same-origin /api which nginx proxies to the backend.
    if (_CONFIGURED_BASE !== _FALLBACK_BASE) {
      console.warn(`[apiFetch] ${_CONFIGURED_BASE} unreachable, falling back to ${_FALLBACK_BASE}`);
      try {
        const r = await fetch(`${_FALLBACK_BASE}${path}`, { ...opts, headers });
        _resolvedBase = _FALLBACK_BASE; // remember fallback works
        return r;
      } catch (fallbackErr) {
        throw fallbackErr;
      }
    }
    throw _networkErr;
  }
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

export default function App() {
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
  const [activeTab, setActiveTab] = useState('portfolio');
  const [positions] = useState(INITIAL_POSITIONS);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [realPositions, setRealPositions] = useState([]);
  const [realPnl, setRealPnl] = useState(0);
  const [cumulativePnl, setCumulativePnl] = useState(0);
  const [hasCumulativePnl, setHasCumulativePnl] = useState(false);
  const [equity, setEquity] = useState(null);
  const [connectorStatus, setConnectorStatus] = useState({ linked: null, online: null, error: null });
  const [engineState, setEngineState] = useState({ autoModeEnabled: true, tradingMode: 'scalping', stackMentorActive: true, riskMode: 'moderate' });
  const [botRunning, setBotRunning] = useState(false);
  const [botBusy, setBotBusy] = useState(false);
  const [botError, setBotError] = useState(null);
  const [showBotStartModal, setShowBotStartModal] = useState(false);

  useEffect(() => {
    document.body.style.overflow = isMobileMenuOpen ? 'hidden' : 'unset';
  }, [isMobileMenuOpen]);

  const handleTelegramLogin = async (telegramUser) => {
    const photoUrl = telegramUser.photo_url ||
      `https://ui-avatars.com/api/?name=${encodeURIComponent(telegramUser.first_name)}&background=d946ef&color=fff&bold=true`;

    // Call backend to verify Telegram auth and get JWT
    try {
      const resp = await fetch(`${API_BASE}/auth/telegram`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(telegramUser),
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.access_token) {
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
          };
          setUser(nextUser);
          try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
        }
      } else {
        const errText = await resp.text().catch(() => '');
        console.error('[Auth] Backend auth failed:', resp.status, errText);
        // Fallback: store user without token (limited functionality)
        const nextUser = { id: String(telegramUser.id), first_name: telegramUser.first_name, username: telegramUser.username || telegramUser.first_name, photo_url: photoUrl, is_premium: false, credits: 0 };
        setUser(nextUser);
        try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
      }
    } catch (err) {
      console.error('[Auth] Network error:', err);
      // Network error fallback
      const nextUser = { id: String(telegramUser.id), first_name: telegramUser.first_name, username: telegramUser.username || telegramUser.first_name, photo_url: photoUrl, is_premium: false, credits: 0 };
      setUser(nextUser);
      try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
    }

    setEngineState({ autoModeEnabled: true, tradingMode: 'scalping', stackMentorActive: true, riskMode: 'moderate', isActive: true, current_balance: 0, total_profit: 0 });
    setRealPositions([]);
    setRealPnl(0);
    setIsLoggedIn(true);
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
    try { localStorage.removeItem('cm_user'); localStorage.removeItem('cm_token'); } catch {}
    setIsLoggedIn(false); setUser(null); setBotRunning(false);
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

  // Hydrate engine running state on login
  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;
    apiFetch('/dashboard/engine/state')
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d && !cancelled) setBotRunning(!!d.running); })
      .catch(() => {});
    return () => { cancelled = true; };
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
          return {
            id: p.positionId || p.id || `${p.symbol}-${i}`,
            pair: p.symbol || p.pair || '—',
            side,
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
          setConnectorStatus({ linked: null, online: false, error: detail });
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
        }
        if (d.engine) {
          setEngineState(prev => ({
            ...prev,
            current_balance: d.engine.current_balance ?? prev.current_balance,
            total_profit: d.engine.total_profit ?? prev.total_profit,
            tradingMode: d.engine.trading_mode || prev.tradingMode,
            stackMentorActive: d.engine.stackmentor_active ?? prev.stackMentorActive,
            autoModeEnabled: d.engine.auto_mode_enabled ?? prev.autoModeEnabled,
            riskMode: d.engine.risk_mode || prev.riskMode,
            isActive: d.engine.is_active ?? prev.isActive,
          }));
        }
      } catch (err) {
        if (!cancelled) setConnectorStatus({ linked: null, online: false, error: `Network error: ${err.message}` });
      }
    };
    load();
    const id = setInterval(load, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [isLoggedIn]);

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
          <p className="text-cyan-400 font-bold tracking-[0.2em] uppercase text-[10px] md:text-xs mb-8 drop-shadow-[0_0_5px_rgba(6,182,212,0.8)]">V2.0 AutoTrade Engine</p>
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
    <div className="min-h-screen bg-[#020202] text-slate-200 font-sans flex flex-col relative overflow-hidden selection:bg-cyan-500/30">
      <div className="fixed inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px] z-0 pointer-events-none" />
      <div className="fixed top-[-10%] left-[-20%] w-[60vw] h-[60vw] rounded-full bg-violet-600/10 blur-[100px] pointer-events-none z-0" />
      <div className="fixed bottom-[-10%] right-[-20%] w-[60vw] h-[60vw] rounded-full bg-cyan-600/10 blur-[100px] pointer-events-none z-0" />

      {/* PROFIT TICKER — sticky top, visible on all devices */}
      <div className="sticky top-0 z-50">
        <ProfitTicker />
      </div>

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

      <div className="flex flex-1 overflow-hidden relative z-10">
        {isMobileMenuOpen && <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden" onClick={() => setIsMobileMenuOpen(false)} />}

        {/* SIDEBAR */}
        <aside className={`fixed inset-y-0 left-0 z-50 w-[280px] md:w-[320px] md:m-6 md:mr-0 bg-[#0a0a0a]/95 md:bg-[#0a0a0a]/80 backdrop-blur-3xl border-r md:border border-white/10 md:rounded-[2.5rem] flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.5)] transition-transform duration-300 ease-in-out transform ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 md:relative md:h-[calc(100vh-3rem)]`}>
          <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />
          <div className="hidden md:flex p-8 items-center gap-4 relative z-10 border-b border-white/5">
            <div className="w-14 h-14 rounded-[1.25rem] bg-gradient-to-tr from-fuchsia-500 via-purple-500 to-cyan-500 p-[1px] shadow-[0_0_20px_rgba(217,70,239,0.3)]"><div className="w-full h-full bg-[#050505] rounded-[19px] flex items-center justify-center"><Bot size={28} className="text-white" /></div></div>
            <div><h1 className="text-2xl font-black text-white tracking-tight leading-tight">CryptoMentor AI</h1><p className="text-cyan-400 text-xs font-bold tracking-[0.2em] uppercase mt-0.5">Your virtual cockpit</p></div>
          </div>
          <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto py-6 relative z-10 custom-scrollbar mt-4 md:mt-0">
            <p className="px-4 text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">AutoTrade Hub</p>
            <NavItem icon={<Activity size={20} />} label="Portfolio Status" active={activeTab === 'portfolio'} onClick={() => navigateTo('portfolio')} />
            <NavItem icon={<Cpu size={20} />} label="Engine Controls" active={activeTab === 'engine'} onClick={() => navigateTo('engine')} />
            <NavItem icon={<BarChart2 size={20} />} label="Performance" active={activeTab === 'performance'} onClick={() => navigateTo('performance')} />
            <NavItem icon={<Settings size={20} />} label="API Bridges" active={activeTab === 'settings'} onClick={() => navigateTo('settings')} />
            <p className="px-4 text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 mt-6">Ecosystem</p>
            <NavItem icon={<Radio size={20} />} label="Signals & Market" active={activeTab === 'signals'} onClick={() => navigateTo('signals')} badge={user.is_premium ? "PRO" : "FREE"} />
            <NavItem icon={<GraduationCap size={20} />} label="Skills & Education" active={activeTab === 'skills'} onClick={() => navigateTo('skills')} />
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
        <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-10 w-full relative z-0 pb-20 md:pb-10 custom-scrollbar">
          {activeTab === 'portfolio' && <PortfolioTab positions={realPositions.length > 0 ? realPositions : []} engineState={engineState} unrealizedPnl={realPnl} cumulativePnl={cumulativePnl} equity={equity} hasRealData={realPositions.length > 0} hasCumulative={hasCumulativePnl} botRunning={botRunning} onToggleBot={handleToggleBot} botBusy={botBusy} connectorStatus={connectorStatus} />}
          {activeTab === 'engine' && <EngineTab engineState={engineState} setEngineState={setEngineState} botRunning={botRunning} onToggleBot={handleToggleBot} />}
          {activeTab === 'performance' && <PerformanceTab />}
          {activeTab === 'settings' && <SettingsTab onBotConnected={handleBotConnected} />}
          {activeTab === 'signals' && <SignalsTab user={user} />}
          {activeTab === 'skills' && <SkillsTab />}
        </main>
      </div>
    </div>
  );
}

function PortfolioTab({ positions, engineState, unrealizedPnl, cumulativePnl, equity, hasRealData, hasCumulative, botRunning, onToggleBot, botBusy, connectorStatus }) {
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

  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
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
      <header className="mb-8 md:mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Portfolio Status</h2>
          <span className="text-slate-400 font-medium text-sm md:text-lg">AI-managed assets overview.</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 bg-white/5 border border-white/10 px-4 py-2.5 rounded-xl backdrop-blur-md">
            <div className="flex flex-col items-end border-r border-white/10 pr-3">
              <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest mb-0.5">Mode</span>
              <span className={`text-xs font-black uppercase tracking-wider ${engineState.tradingMode === 'scalping' ? 'text-fuchsia-400' : 'text-cyan-400'}`}>{engineState.tradingMode || 'scalping'}</span>
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
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
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
            {positions.map(pos => <PositionCard key={pos.id} position={pos} stackMentorActive={engineState.stackMentorActive} />)}
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

function EngineTab({ engineState, setEngineState, botRunning, onToggleBot }) {
  return (
    <div className="max-w-4xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Engine Controls</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Configure AutoTrade behavior, StackMentor, and Risk models.</p></header>

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl border ${engineState.autoModeEnabled ? 'border-fuchsia-500/50 shadow-[0_0_40px_rgba(217,70,239,0.15)]' : 'border-white/10'} rounded-[1.5rem] md:rounded-[2.5rem] p-6 md:p-8 relative overflow-hidden transition-all duration-500 group`}>
          {engineState.autoModeEnabled && <div className="absolute top-0 right-0 w-32 h-32 bg-fuchsia-500/10 blur-[40px] rounded-full pointer-events-none" />}
          <div className="flex justify-between items-start mb-5 relative z-10">
            <div className="p-2.5 bg-white/5 rounded-xl border border-white/5"><RefreshCw className={engineState.autoModeEnabled ? "text-fuchsia-400 animate-spin-slow w-6 h-6" : "text-slate-500 w-6 h-6"} /></div>
            <button onClick={() => setEngineState({...engineState, autoModeEnabled: !engineState.autoModeEnabled})} className="p-1 -m-1 transition-transform active:scale-90">{engineState.autoModeEnabled ? <ToggleRight className="text-fuchsia-500 w-9 h-9" /> : <ToggleLeft className="text-slate-600 w-9 h-9" />}</button>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-white mb-2 relative z-10">Auto Mode Switcher</h3>
          <p className="text-slate-400 text-xs md:text-sm font-medium leading-relaxed relative z-10 mb-6">Automatically switches between Scalping and Swing trading modes based on real-time AI market sentiment detection.</p>
          {!engineState.autoModeEnabled && (
            <div className="bg-white/5 p-4 rounded-xl border border-white/10 relative z-10">
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-3">Manual Override</p>
              <div className="flex gap-2">
                <button onClick={() => setEngineState({...engineState, tradingMode: 'scalping'})} className={`flex-1 py-3 rounded-lg font-bold text-xs transition-all ${engineState.tradingMode === 'scalping' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'bg-[#050505] text-slate-400 border border-white/5'}`}>SCALPING</button>
                <button onClick={() => setEngineState({...engineState, tradingMode: 'swing'})} className={`flex-1 py-3 rounded-lg font-bold text-xs transition-all ${engineState.tradingMode === 'swing' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-[#050505] text-slate-400 border border-white/5'}`}>SWING</button>
              </div>
            </div>
          )}
        </div>
        <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl border ${engineState.stackMentorActive ? 'border-cyan-500/50 shadow-[0_0_40px_rgba(6,182,212,0.15)]' : 'border-white/10'} rounded-[1.5rem] md:rounded-[2.5rem] p-6 md:p-8 relative overflow-hidden transition-all duration-500 group`}>
          {engineState.stackMentorActive && <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 blur-[40px] rounded-full pointer-events-none" />}
          <div className="flex justify-between items-start mb-5 relative z-10">
            <div className="p-2.5 bg-white/5 rounded-xl border border-white/5"><Layers className={engineState.stackMentorActive ? "text-cyan-400 w-6 h-6" : "text-slate-500 w-6 h-6"} /></div>
            <button onClick={() => setEngineState({...engineState, stackMentorActive: !engineState.stackMentorActive})} className="p-1 -m-1 transition-transform active:scale-90">{engineState.stackMentorActive ? <ToggleRight className="text-cyan-500 w-9 h-9" /> : <ToggleLeft className="text-slate-600 w-9 h-9" />}</button>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-white mb-2 relative z-10">StackMentor Tracking</h3>
          <p className="text-slate-400 text-xs md:text-sm font-medium leading-relaxed relative z-10 mb-6">Enables 3-Tier partial Take Profit (TP1, TP2, TP3) system and automatically moves Stop Loss to breakeven after TP1.</p>
          <div className={`space-y-2.5 relative z-10 transition-all duration-300 ${!engineState.stackMentorActive ? 'opacity-40 grayscale pointer-events-none' : ''}`}>
            {[{label:'TP1: Scale out 30%', color:'cyan'},{label:'TP2: Scale out 40%', color:'cyan'},{label:'TP3: Runner 30% (SL Breakeven)', color:'fuchsia'}].map((tp, i) => (
              <div key={i} className="flex items-center gap-3 bg-[#050505] border border-white/5 p-3 rounded-xl">
                <div className={`w-2.5 h-2.5 rounded-full ${engineState.stackMentorActive ? (tp.color === 'cyan' ? 'bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]' : 'bg-fuchsia-400 shadow-[0_0_8px_rgba(217,70,239,0.8)]') : 'bg-slate-700'}`} />
                <span className="text-xs font-bold text-slate-300">{tp.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
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
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Failed to connect. Make sure your keys only have Trade permission.');
      
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
      const data = await resp.json();
      if (!resp.ok || !data.success) throw new Error(data.message || data.detail || 'Test failed.');
      
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
              logo="U" 
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

function SignalsTab({ user }) {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const r = await apiFetch('/dashboard/signals');
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
  }, []);

  const stamp = updatedAt ? updatedAt.toLocaleTimeString('en-GB', { timeZone: 'Asia/Singapore', hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' UTC+8' : '—';

  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">AI Intelligence Hub</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Real-time market analysis and algorithmic signals. <span className="text-slate-500">Updated {stamp}</span></p></div>
        <div className="flex items-center gap-2 bg-fuchsia-500/10 border border-fuchsia-500/20 px-4 py-2.5 rounded-xl backdrop-blur-md"><div className="relative flex h-2.5 w-2.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fuchsia-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-fuchsia-500"></span></div><span className="text-xs font-bold text-fuchsia-400 tracking-[0.1em] uppercase">{loading ? 'Loading' : 'Scanning Markets'}</span></div>
      </header>
      {error && <div className="text-rose-400 text-sm font-bold bg-rose-500/10 border border-rose-500/20 px-4 py-3 rounded-xl">Failed to load live signals: {error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {signals.map((signal, idx) => (
          <div key={signal.id || signal.pair} className="animate-in fade-in slide-in-from-bottom-8" style={{ animationDelay: `${idx * 150}ms`, animationFillMode: 'both' }}>
            <SignalCard signal={signal} userIsPremium={user?.is_premium} />
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

// --- SUBCOMPONENTS ---
function NavItem({ icon, label, active, onClick, badge }) {
  return (
    <button onClick={onClick} className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 font-bold text-sm relative overflow-hidden group ${active ? 'text-white' : 'text-slate-400 hover:text-white'}`}>
      {active && <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent border border-white/10 shadow-[inset_3px_0_0_0_rgba(255,255,255,1)] rounded-xl z-0" />}
      {!active && <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl z-0" />}
      <div className="flex items-center gap-3 w-full">
        <div className={`relative z-10 transition-transform duration-300 group-hover:scale-110 ${active ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`}>{icon}</div>
        <span className="relative z-10 tracking-wide text-left truncate">{label}</span>
      </div>
      {badge && <span className={`relative z-10 text-[8px] font-black tracking-widest px-1.5 py-0.5 rounded border shrink-0 ml-2 ${badge === 'PRO' ? 'text-fuchsia-300 bg-fuchsia-500/20 border-fuchsia-500/30' : 'text-cyan-300 bg-cyan-500/20 border-cyan-500/30'}`}>{badge}</span>}
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

function PositionCard({ position, stackMentorActive }) {
  // Normalize: API returns "BUY"/"SELL", mock data uses "LONG"/"SHORT"
  const isLong = position.side === 'LONG' || position.side === 'BUY';
  const sideLabel = isLong ? 'LONG' : 'SHORT';
  return (
    <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-7 flex flex-col transition-all duration-500 md:hover:-translate-y-1 hover:border-white/20 relative overflow-hidden group">
      <div className={`absolute top-0 left-0 w-1.5 h-full ${isLong ? 'bg-gradient-to-b from-lime-400 to-lime-600' : 'bg-gradient-to-b from-rose-400 to-rose-600'}`} />
      <div className="pl-3 relative z-10 flex flex-col h-full">
        <div className="flex flex-col sm:flex-row justify-between items-start mb-5 gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h4 className="text-white font-black text-xl tracking-tight">{position.pair}</h4>
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

function BridgeCard({ name, status, logo, colors, onConnect, onDisconnect, loading }) {
  const isSynced = status === 'synced';
  return (
    <div className="border border-white/10 rounded-2xl p-4 md:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white/[0.02] hover:bg-white/[0.04] transition-all hover:border-white/20 group">
      <div className="flex items-center gap-4 w-full">
        <div className={`w-12 h-12 md:w-16 md:h-16 bg-gradient-to-br ${colors} rounded-xl flex items-center justify-center font-black text-white text-xl shadow-lg shrink-0`}>{logo}</div>
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

function SignalCard({ signal, userIsPremium }) {
  const [isPlaced, setIsPlaced] = useState(false);
  const [placing, setPlacing] = useState(false);
  const [placeError, setPlaceError] = useState(null);
  const [now, setNow] = useState(() => Date.now());
  const isLong = signal.direction === 'LONG';
  const isLocked = signal.premium && !userIsPremium;
  const isExpired = !!signal.expired;

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const windowMs = (signal.entry_window_seconds || 300) * 1000;
  const generatedMs = signal.generated_at ? Date.parse(signal.generated_at) : now;
  const ageMs = Math.max(0, now - generatedMs);
  const remainingMs = Math.max(0, windowMs - ageMs);
  const windowExpired = remainingMs <= 0;
  const remainingLabel = windowExpired
    ? 'Entry window closed'
    : `${Math.floor(remainingMs / 60000)}:${String(Math.floor((remainingMs % 60000) / 1000)).padStart(2, '0')} left`;

  const handleExecute = async () => {
    if (placing || isPlaced || windowExpired) return;
    setPlacing(true);
    setPlaceError(null);
    try {
      const r = await apiFetch('/dashboard/signals/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: signal.pair.replace('/', ''),
          generated_at: signal.generated_at,
        }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
      setIsPlaced(true);
    } catch (e) {
      setPlaceError(e.message || 'Failed to place order');
    } finally {
      setPlacing(false);
    }
  };

  return (
    <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-6 flex flex-col transition-all duration-500 relative overflow-hidden group hover:border-white/20 ${isLocked ? 'opacity-80' : ''} ${isExpired ? 'opacity-60 grayscale' : ''}`}>
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
          <div className="text-[10px] font-bold text-fuchsia-400 bg-fuchsia-500/10 px-2 py-0.5 rounded border border-fuchsia-500/20">{signal.confidence}% AI CONF</div>
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
                <p className="text-xs text-slate-400">Autotrade is holding this trade.</p>
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
          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-widest mt-1">
            <span className="text-slate-500">Entry Window</span>
            <span className={windowExpired ? 'text-rose-400' : remainingMs < 60000 ? 'text-amber-400' : 'text-cyan-400'}>{remainingLabel}</span>
          </div>
          <button onClick={handleExecute} disabled={isPlaced || placing || windowExpired} className={`mt-1 w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${isPlaced ? 'bg-lime-500/20 text-lime-400 border border-lime-500/30' : windowExpired ? 'bg-white/5 text-slate-500 border border-white/10' : isLong ? 'bg-lime-500/10 text-lime-400 hover:bg-lime-500/20 border border-lime-500/20' : 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20'}`}>
            {isPlaced ? <><CheckCircle2 size={16} /> Position Opened</> : placing ? <><Zap size={16} /> Placing…</> : windowExpired ? <>Entry Window Closed</> : <><Zap size={16} /> 1-Click Open {signal.direction}</>}
          </button>
          {placeError && <p className="text-[10px] font-bold text-rose-400 mt-1">{placeError}</p>}
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
