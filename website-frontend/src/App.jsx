import React, { useState, useEffect } from 'react';
import {
  LineChart, Wallet, Bot, Settings, LogOut,
  TrendingUp, TrendingDown, Activity, CheckCircle2,
  Shield, BarChart2, Target, Zap, Layers, RefreshCw,
  GraduationCap, Radio, Cpu, ToggleRight, ToggleLeft,
  Menu, X, Crosshair, ArrowUpRight, ArrowDownRight,
  PlayCircle, BookOpen, Lock, Clock
} from 'lucide-react';

const INITIAL_POSITIONS = [
  { id: 1, pair: "BTC/USDT", side: "LONG", entry: "$64,230.50", current: "$65,100.00", margin: "$1,000", leverage: "10x", pnl: "+$124.50", pnlPercent: "+12.45%", isProfitable: true, tp: { tp1: { price: "$64,800", hit: true }, tp2: { price: "$65,500", hit: false }, tp3: { price: "$66,000", hit: false } } },
  { id: 2, pair: "SOL/USDT", side: "SHORT", entry: "$145.20", current: "$142.10", margin: "$500", leverage: "5x", pnl: "+$31.00", pnlPercent: "+6.20%", isProfitable: true, tp: { tp1: { price: "$143.00", hit: true }, tp2: { price: "$141.50", hit: false }, tp3: { price: "$138.00", hit: false } } },
  { id: 3, pair: "ETH/USDT", side: "LONG", entry: "$3,105.00", current: "$3,080.20", margin: "$800", leverage: "5x", pnl: "-$19.84", pnlPercent: "-2.48%", isProfitable: false, tp: { tp1: { price: "$3,150", hit: false }, tp2: { price: "$3,200", hit: false }, tp3: { price: "$3,300", hit: false } } },
];

const PERFORMANCE_METRICS = { sharpeRatio: "2.14", maxDrawdown: "-12.4%", winRate: "68.5%", totalTrades: "1,248", projected1Yr: "$24,500.00", monthlyVolatility: "4.2%" };

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
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('portfolio');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [realPositions, setRealPositions] = useState([]);
  const [realPnl, setRealPnl] = useState(0);
  const [liveBalance, setLiveBalance] = useState(null);
  const [liveUnrealizedPnl, setLiveUnrealizedPnl] = useState(null);
  const [bitunixLinked, setBitunixLinked] = useState(false);
  const [engineState, setEngineState] = useState({ autoModeEnabled: true, tradingMode: 'scalping', stackMentorActive: true, riskMode: 'moderate' });

  useEffect(() => {
    document.body.style.overflow = isMobileMenuOpen ? 'hidden' : 'unset';
  }, [isMobileMenuOpen]);

  const handleTelegramLogin = (telegramUser) => {
    // /api/ di-proxy oleh nginx ke backend port 8000
    fetch('/api/auth/telegram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(telegramUser),
    })
      .then(res => res.ok ? res.json() : res.text().then(t => Promise.reject(t)))
      .then(data => {
        localStorage.setItem('cm_token', data.access_token);
        const token = data.access_token;
        // Fetch real dashboard data
        return fetch('/api/dashboard/portfolio', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
          .then(r => r.json())
          .then(dashboard => {
            const u = dashboard.user;
            setUser({
              id: String(u.telegram_id),
              first_name: u.first_name || telegramUser.first_name,
              username: u.username || telegramUser.username,
              photo_url: telegramUser.photo_url || `https://ui-avatars.com/api/?name=${u.first_name}&background=d946ef&color=fff`,
              is_premium: u.is_premium || false,
              credits: u.credits || 0,
            });
            setEngineState({
              autoModeEnabled: dashboard.engine.auto_mode_enabled,
              tradingMode: dashboard.engine.trading_mode || 'scalping',
              stackMentorActive: dashboard.engine.stackmentor_active,
              riskMode: dashboard.engine.risk_mode || 'moderate',
              isActive: dashboard.engine.is_active,
            });
            setRealPnl(dashboard.portfolio.pnl_30d || 0);

            // Fetch live Bitunix data jika API keys tersambung
            if (dashboard.bitunix?.linked) {
              setBitunixLinked(true);
              fetch('/api/bitunix/portfolio', {
                headers: { 'Authorization': `Bearer ${token}` }
              })
                .then(r => r.ok ? r.json() : null)
                .then(bx => {
                  if (bx) {
                    setLiveBalance(bx.account?.balance ?? 0);
                    setLiveUnrealizedPnl(bx.unrealized_pnl ?? 0);
                    const mapped = (bx.positions || []).map((p, i) => ({
                      id: i + 1,
                      pair: p.symbol || p.pair || 'UNKNOWN',
                      side: (p.side || p.direction || 'LONG').toUpperCase(),
                      entry: `$${parseFloat(p.entry_price || p.entryPrice || 0).toFixed(2)}`,
                      current: `$${parseFloat(p.mark_price || p.markPrice || p.entry_price || 0).toFixed(2)}`,
                      margin: `$${parseFloat(p.margin || p.initial_margin || 0).toFixed(2)}`,
                      leverage: `${p.leverage || 1}x`,
                      pnl: `${parseFloat(p.pnl || p.unrealized_pnl || 0) >= 0 ? '+' : ''}$${parseFloat(p.pnl || p.unrealized_pnl || 0).toFixed(2)}`,
                      pnlPercent: `${parseFloat(p.pnl_pct || p.roe || 0) >= 0 ? '+' : ''}${parseFloat(p.pnl_pct || p.roe || 0).toFixed(2)}%`,
                      isProfitable: parseFloat(p.pnl || p.unrealized_pnl || 0) >= 0,
                      tp: { tp1: { price: '-', hit: false }, tp2: { price: '-', hit: false }, tp3: { price: '-', hit: false } }
                    }));
                    setRealPositions(mapped);
                  }
                })
                .catch(() => {});
            } else {
              // Fallback ke data Supabase
              setRealPositions(dashboard.portfolio.positions || []);
            }
            setIsLoggedIn(true);
          });
      })
      .catch(err => {
        console.error('Auth error:', err);
        alert('Login gagal: ' + err);
      });
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

  const handleLogout = () => { setIsLoggedIn(false); setUser(null); };
  const navigateTo = (tab) => { setActiveTab(tab); setIsMobileMenuOpen(false); };

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

      <div className="flex flex-1 overflow-hidden relative z-10">
        {isMobileMenuOpen && <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden" onClick={() => setIsMobileMenuOpen(false)} />}

        {/* SIDEBAR */}
        <aside className={`fixed inset-y-0 left-0 z-50 w-[280px] md:w-[320px] md:m-6 md:mr-0 bg-[#0a0a0a]/95 md:bg-[#0a0a0a]/80 backdrop-blur-3xl border-r md:border border-white/10 md:rounded-[2.5rem] flex flex-col shadow-[0_0_50px_rgba(0,0,0,0.5)] transition-transform duration-300 ease-in-out transform ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0 md:relative md:h-[calc(100vh-3rem)]`}>
          <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />
          <div className="hidden md:flex p-8 items-center gap-4 relative z-10 border-b border-white/5">
            <div className="w-14 h-14 rounded-[1.25rem] bg-gradient-to-tr from-fuchsia-500 via-purple-500 to-cyan-500 p-[1px] shadow-[0_0_20px_rgba(217,70,239,0.3)]"><div className="w-full h-full bg-[#050505] rounded-[19px] flex items-center justify-center"><Bot size={28} className="text-white" /></div></div>
            <div><h1 className="text-2xl font-black text-white tracking-tight leading-tight">CryptoMentor</h1><p className="text-cyan-400 text-xs font-bold tracking-[0.2em] uppercase mt-0.5">AI System v2.0</p></div>
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
          <div className="p-5 md:p-6 mt-auto relative z-10 border-t border-white/5">
            <div className="flex items-center gap-3 p-3 rounded-[1.5rem] bg-white/[0.03] border border-white/5 mb-4">
              <div className="relative shrink-0">
                <img src={user.photo_url} alt="Profile" className="w-10 h-10 rounded-[1rem] object-cover ring-2 ring-fuchsia-500/30" />
                {user.is_premium && <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-tr from-fuchsia-500 to-cyan-500 rounded-full border-2 border-[#0a0a0a] flex items-center justify-center"><span className="text-[6px] text-white font-black">PRO</span></div>}
              </div>
              <div className="overflow-hidden flex-1"><p className="text-sm font-bold text-white truncate">{user.first_name}</p><p className="text-xs text-slate-400 truncate">@{user.username}</p></div>
            </div>
            <button onClick={handleLogout} className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-bold text-rose-400 hover:text-white hover:bg-rose-500/90 border border-rose-500/20 rounded-xl transition-all"><LogOut size={16} /> Disconnect</button>
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 lg:p-10 w-full relative z-0 pb-20 md:pb-10 custom-scrollbar">
          {activeTab === 'portfolio' && <PortfolioTab positions={bitunixLinked ? realPositions : (realPositions.length > 0 ? realPositions : INITIAL_POSITIONS)} engineState={engineState} pnl30d={realPnl} hasRealData={bitunixLinked || realPositions.length > 0} liveBalance={liveBalance} liveUnrealizedPnl={liveUnrealizedPnl} bitunixLinked={bitunixLinked} />}
          {activeTab === 'engine' && <EngineTab engineState={engineState} setEngineState={setEngineState} />}
          {activeTab === 'performance' && <PerformanceTab />}
          {activeTab === 'settings' && <SettingsTab />}
          {activeTab === 'signals' && <SignalsTab user={user} />}
          {activeTab === 'skills' && <SkillsTab />}
        </main>
      </div>
    </div>
  );
}

function PortfolioTab({ positions, engineState, pnl30d, hasRealData, liveBalance, liveUnrealizedPnl, bitunixLinked }) {
  const balanceDisplay = liveBalance !== null
    ? `$${parseFloat(liveBalance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '$0.00';

  const pnlDisplay = hasRealData
    ? (pnl30d >= 0 ? `+$${pnl30d.toFixed(2)}` : `-$${Math.abs(pnl30d).toFixed(2)}`)
    : (liveUnrealizedPnl !== null
        ? (liveUnrealizedPnl >= 0 ? `+$${liveUnrealizedPnl.toFixed(2)}` : `-$${Math.abs(liveUnrealizedPnl).toFixed(2)}`)
        : '$0.00');

  const pnlPct = '';
  const isPnlPositive = pnl30d >= 0 || (liveUnrealizedPnl !== null && liveUnrealizedPnl >= 0);
  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Portfolio Status</h2><span className="text-slate-400 font-medium text-sm md:text-lg">AI-managed assets overview.</span></div>
        <div className="flex items-center gap-3 bg-white/5 border border-white/10 px-4 py-2.5 rounded-xl backdrop-blur-md">
          <div className="flex flex-col items-end border-r border-white/10 pr-3"><span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest mb-0.5">Current Mode</span><span className={`text-xs font-black uppercase tracking-wider ${engineState.tradingMode === 'scalping' ? 'text-fuchsia-400' : 'text-cyan-400'}`}>{engineState.tradingMode}</span></div>
          <div className="flex items-center gap-2"><span className="relative flex h-2.5 w-2.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-lime-400 shadow-[0_0_10px_rgba(163,230,53,0.8)]"></span></span><span className="text-[10px] font-bold text-lime-400 tracking-[0.1em] uppercase">Engine Active</span></div>
        </div>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        <StatCard title="Total Balance" value={liveBalance !== null ? balanceDisplay : '$0.00'} icon={<Wallet className="text-cyan-400 w-6 h-6" />} glowColor="cyan" />
        <StatCard title="Total PnL (30d)" value={pnlDisplay} subtext={pnlPct} isPositive={isPnlPositive} icon={<TrendingUp className="text-lime-400 w-6 h-6" />} glowColor="lime" />
        <StatCard title="Open Positions" value={positions.length > 0 && hasRealData ? positions.length.toString() : (bitunixLinked ? positions.length.toString() : '0')} icon={<Target className="text-fuchsia-400 w-6 h-6" />} glowColor="fuchsia" />
      </div>
      <div className="pt-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
          <h3 className="text-xl md:text-2xl font-black text-white tracking-tight flex items-center gap-3">Current Opened Positions <span className="px-2.5 py-1 rounded-lg bg-white/10 text-white/60 text-xs font-bold">{positions.length}</span></h3>
          {engineState.stackMentorActive && <div className="w-fit flex items-center gap-2 text-xs font-bold text-fuchsia-400 bg-fuchsia-500/10 px-3 py-1.5 rounded-lg border border-fuchsia-500/20"><Layers size={14} /> STACKMENTOR TRACKING</div>}
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 md:gap-6">
          {positions.length > 0 ? (
            positions.map(pos => <PositionCard key={pos.id} position={pos} stackMentorActive={engineState.stackMentorActive} />)
          ) : (
            <div className="col-span-2 bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] border border-white/5 p-10 flex flex-col items-center justify-center text-center">
              <Target className="text-slate-600 w-12 h-12 mb-4" />
              <p className="text-slate-400 font-bold text-lg mb-1">No Open Positions</p>
              <p className="text-slate-600 text-sm">{bitunixLinked ? 'No active trades on Bitunix right now.' : 'Connect your Bitunix API via the Telegram bot to see live positions.'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EngineTab({ engineState, setEngineState }) {
  return (
    <div className="max-w-4xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Engine Controls</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Configure AutoTrade behavior, StackMentor, and Risk models.</p></header>
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
  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">PnL Performance</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Advanced metrics and historical analytics.</p></header>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6">
        <MiniStat title="Sharpe" value={PERFORMANCE_METRICS.sharpeRatio} subtitle="Risk-Adjusted Return" highlight="text-cyan-400" glow="cyan" />
        <MiniStat title="Max DD" value={PERFORMANCE_METRICS.maxDrawdown} subtitle="Historical Peak-to-Trough" highlight="text-rose-400" glow="rose" />
        <MiniStat title="Win Rate" value={PERFORMANCE_METRICS.winRate} subtitle={`${PERFORMANCE_METRICS.totalTrades} Trades`} highlight="text-lime-400" glow="lime" />
        <MiniStat title="Volatility" value={PERFORMANCE_METRICS.monthlyVolatility} subtitle="Average fluctuation" highlight="text-fuchsia-400" glow="fuchsia" />
      </div>
      <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-white/5 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-8 relative overflow-hidden flex flex-col min-h-[300px] md:min-h-[450px] group">
        <div className="absolute top-0 right-0 w-[80%] h-[80%] bg-cyan-500/10 blur-[80px] rounded-full pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity duration-700" />
        <h3 className="text-sm md:text-xl font-bold text-white flex items-center gap-2 bg-white/5 px-3 py-2 rounded-lg border border-white/5 w-fit z-10 mb-6"><LineChart className="text-cyan-400 w-4 h-4" /> Cumulative Equity</h3>
        <div className="flex-1 relative z-10 w-full h-full">
          <svg viewBox="0 0 1000 300" className="w-full h-full drop-shadow-[0_0_20px_rgba(6,182,212,0.3)]" preserveAspectRatio="none">
            <defs>
              <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="rgba(6,182,212,0.4)" /><stop offset="100%" stopColor="rgba(6,182,212,0.0)" /></linearGradient>
              <filter id="glow"><feGaussianBlur stdDeviation="4" result="coloredBlur"/><feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
            </defs>
            <path d="M0,300 L0,220 Q100,240 200,160 T400,110 T600,190 T800,70 T1000,40 L1000,300 Z" fill="url(#chart-grad)" />
            <path d="M0,220 Q100,240 200,160 T400,110 T600,190 T800,70 T1000,40" fill="none" stroke="#06b6d4" strokeWidth="4" filter="url(#glow)" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="1000" cy="40" r="6" fill="#fff" className="animate-pulse" />
            <circle cx="1000" cy="40" r="14" fill="none" stroke="#06b6d4" strokeWidth="2" className="animate-ping opacity-50" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function SettingsTab() {
  return (
    <div className="max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12"><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">API Bridges</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Securely link your liquidity providers to CryptoMentor AI.</p></header>
      <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl border border-white/5 rounded-[1.5rem] md:rounded-[2.5rem] p-5 md:p-12 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-bl from-orange-500/5 to-transparent pointer-events-none" />
        <div className="relative p-4 md:p-6 bg-orange-500/10 border border-orange-500/20 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="p-2 bg-orange-500/20 rounded-xl shrink-0 border border-orange-500/30 w-fit"><Shield className="text-orange-400 w-6 h-6" /></div>
          <div><h4 className="text-orange-400 font-bold text-xs tracking-wider uppercase mb-1">Security Protocol</h4><p className="text-orange-200/80 font-medium leading-relaxed text-xs">Ensure your API keys have <strong className="text-white">Withdrawals DISABLED</strong>. The AI engine only requires execution and read privileges.</p></div>
        </div>
        <div className="space-y-3 relative z-10 mt-6">
          <BridgeCard name="Bitunix" status="synced" logo="U" colors="from-blue-500 to-indigo-600" />
        </div>
      </div>
    </div>
  );
}

function SignalsTab({ user }) {
  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">AI Intelligence Hub</h2><p className="text-slate-400 font-medium text-sm md:text-lg">Real-time market analysis and algorithmic signals.</p></div>
        <div className="flex items-center gap-2 bg-fuchsia-500/10 border border-fuchsia-500/20 px-4 py-2.5 rounded-xl backdrop-blur-md"><div className="relative flex h-2.5 w-2.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fuchsia-400 opacity-75"></span><span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-fuchsia-500"></span></div><span className="text-xs font-bold text-fuchsia-400 tracking-[0.1em] uppercase">Scanning Markets</span></div>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
        {MOCK_SIGNALS.map((signal, idx) => (
          <div key={signal.id} className="animate-in fade-in slide-in-from-bottom-8" style={{ animationDelay: `${idx * 150}ms`, animationFillMode: 'both' }}>
            <SignalCard signal={signal} userIsPremium={user?.is_premium} />
          </div>
        ))}
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
  const isLong = position.side === 'LONG';
  return (
    <div className="bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-7 flex flex-col transition-all duration-500 md:hover:-translate-y-1 hover:border-white/20 relative overflow-hidden group">
      <div className={`absolute top-0 left-0 w-1.5 h-full ${isLong ? 'bg-gradient-to-b from-lime-400 to-lime-600' : 'bg-gradient-to-b from-rose-400 to-rose-600'}`} />
      <div className="pl-3 relative z-10 flex flex-col h-full">
        <div className="flex flex-col sm:flex-row justify-between items-start mb-5 gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h4 className="text-white font-black text-xl tracking-tight">{position.pair}</h4>
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-black tracking-wider ${isLong ? 'bg-lime-500/10 text-lime-400 border border-lime-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                {isLong ? <TrendingUp size={12} /> : <TrendingDown size={12} />} {position.side} • {position.leverage}
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

function BridgeCard({ name, status, logo, colors }) {
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
      <button className={`w-full sm:w-auto font-bold px-6 py-3 border rounded-xl transition-all text-sm ${isSynced ? 'text-white border-white/10 bg-white/5 hover:bg-white/10' : 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20'}`}>{isSynced ? 'Configure' : 'Connect'}</button>
    </div>
  );
}

function SignalCard({ signal, userIsPremium }) {
  const [isPlaced, setIsPlaced] = useState(false);
  const isLong = signal.direction === 'LONG';
  const isLocked = signal.premium && !userIsPremium;
  return (
    <div className={`bg-[#0a0a0a]/60 backdrop-blur-2xl rounded-[1.5rem] md:rounded-[2rem] border border-white/5 p-5 md:p-6 flex flex-col transition-all duration-500 relative overflow-hidden group hover:border-white/20 ${isLocked ? 'opacity-80' : ''}`}>
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
      {isLocked ? (
        <div className="flex-1 flex flex-col items-center justify-center py-6 bg-white/[0.02] rounded-xl border border-white/5 mt-2"><Lock className="text-fuchsia-500 w-8 h-8 mb-2 opacity-80" /><p className="text-sm font-bold text-white mb-1">Premium Signal</p><p className="text-xs text-slate-400">Upgrade to access targets.</p></div>
      ) : (
        <div className="flex flex-col gap-3 mt-2">
          <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5"><p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1 flex items-center gap-1.5"><Crosshair size={10} /> Entry Zone</p><p className="text-white font-bold text-sm">{signal.entry}</p></div>
          <div className="flex gap-2">
            <div className="flex-1 bg-white/[0.02] p-3 rounded-xl border border-white/5"><p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Stack Targets</p><div className="flex flex-wrap gap-1">{signal.targets.map((t, i) => <span key={i} className="text-xs font-bold text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">TP{i+1}: {t}</span>)}</div></div>
            <div className="bg-white/[0.02] p-3 rounded-xl border border-white/5 min-w-[80px]"><p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Stop Loss</p><p className="text-rose-400 font-bold text-sm">{signal.stopLoss}</p></div>
          </div>
          <button onClick={() => { if (!isPlaced) { setIsPlaced(true); setTimeout(() => setIsPlaced(false), 3000); } }} disabled={isPlaced} className={`mt-2 w-full py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all ${isPlaced ? 'bg-lime-500/20 text-lime-400 border border-lime-500/30' : isLong ? 'bg-lime-500/10 text-lime-400 hover:bg-lime-500/20 border border-lime-500/20' : 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20'}`}>
            {isPlaced ? <><CheckCircle2 size={16} /> Position Opened</> : <><Zap size={16} /> 1-Click Open {signal.direction}</>}
          </button>
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
