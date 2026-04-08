#!/usr/bin/env python3
"""Patch App.jsx: fix auth to get JWT token + fix PortfolioTab"""

content = open('website-frontend/src/App.jsx', 'r', encoding='utf-8').read()
lines = content.split('\n')

# ── 1. Find and replace handleTelegramLogin (DEV MODE → real auth) ──────────
# Find the line with "const handleTelegramLogin"
start_idx = None
for i, l in enumerate(lines):
    if 'const handleTelegramLogin = (telegramUser) => {' in l:
        start_idx = i
        break

if start_idx is None:
    print("ERROR: handleTelegramLogin not found")
    exit(1)

# Find closing brace of this function (count braces)
depth = 0
end_idx = None
for i in range(start_idx, len(lines)):
    depth += lines[i].count('{') - lines[i].count('}')
    if depth == 0 and i > start_idx:
        end_idx = i
        break

print(f"handleTelegramLogin: lines {start_idx+1}-{end_idx+1}")

new_login = r"""  const handleTelegramLogin = async (telegramUser) => {
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
        // Fallback: store user without token (limited functionality)
        const nextUser = { id: String(telegramUser.id), first_name: telegramUser.first_name, username: telegramUser.username || telegramUser.first_name, photo_url: photoUrl, is_premium: false, credits: 0 };
        setUser(nextUser);
        try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
      }
    } catch {
      // Network error fallback
      const nextUser = { id: String(telegramUser.id), first_name: telegramUser.first_name, username: telegramUser.username || telegramUser.first_name, photo_url: photoUrl, is_premium: false, credits: 0 };
      setUser(nextUser);
      try { localStorage.setItem('cm_user', JSON.stringify(nextUser)); } catch {}
    }

    setEngineState({ autoModeEnabled: true, tradingMode: 'scalping', stackMentorActive: true, riskMode: 'moderate', isActive: true, current_balance: 0, total_profit: 0 });
    setRealPositions([]);
    setRealPnl(0);
    setIsLoggedIn(true);
  };"""

lines[start_idx:end_idx+1] = new_login.split('\n')
print(f"Replaced handleTelegramLogin ({end_idx - start_idx + 1} lines → {len(new_login.split(chr(10)))} lines)")

# ── 2. Fix handleLogout to also clear token ──────────────────────────────────
content2 = '\n'.join(lines)
content2 = content2.replace(
    "try { localStorage.removeItem('cm_user'); } catch {}\n    setIsLoggedIn(false); setUser(null); setBotRunning(false);",
    "try { localStorage.removeItem('cm_user'); localStorage.removeItem('cm_token'); } catch {}\n    setIsLoggedIn(false); setUser(null); setBotRunning(false);"
)
lines = content2.split('\n')

# ── 3. Fix PortfolioTab ──────────────────────────────────────────────────────
# Find PortfolioTab function
pt_start = None
for i, l in enumerate(lines):
    if 'function PortfolioTab(' in l:
        pt_start = i
        break

if pt_start is None:
    print("ERROR: PortfolioTab not found")
    exit(1)

# Find the closing </div> of the stat cards grid + header section
# We need to replace from function signature to end of stat cards grid
# Find the line with "Open Positions" StatCard
stat_end = None
for i in range(pt_start, pt_start + 60):
    if 'Open Positions' in lines[i] and 'StatCard' in lines[i]:
        stat_end = i
        break

if stat_end is None:
    print("ERROR: Open Positions StatCard not found")
    exit(1)

print(f"PortfolioTab stat section: lines {pt_start+1}-{stat_end+1}")

new_portfolio_head = r"""function PortfolioTab({ positions, engineState, unrealizedPnl, cumulativePnl, equity, hasRealData, hasCumulative, botRunning, onToggleBot, botBusy }) {
  const pnlAbs = Math.abs(unrealizedPnl).toFixed(2);
  const pnlDisplay = hasRealData ? `${unrealizedPnl >= 0 ? '+' : '-'}$${pnlAbs}` : '$0.00';
  const realizedAbs = Math.abs(cumulativePnl).toFixed(2);
  const realizedDisplay = `${cumulativePnl >= 0 ? '+' : '-'}$${realizedAbs}`;
  const equityDisplay = equity !== null && equity !== undefined ? `$${Number(equity).toFixed(2)}` : '—';

  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
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
"""

lines[pt_start:stat_end+1] = new_portfolio_head.split('\n')
print(f"Replaced PortfolioTab header ({stat_end - pt_start + 1} lines → {len(new_portfolio_head.split(chr(10)))} lines)")

# ── 4. Fix PortfolioTab call in main render to pass botBusy ─────────────────
content3 = '\n'.join(lines)
content3 = content3.replace(
    "activeTab === 'portfolio' && <PortfolioTab positions={realPositions.length > 0 ? realPositions : INITIAL_POSITIONS} engineState={engineState} unrealizedPnl={realPnl} cumulativePnl={cumulativePnl} equity={equity} hasRealData={realPositions.length > 0} hasCumulative={hasCumulativePnl} botRunning={botRunning} onToggleBot={handleToggleBot} />",
    "activeTab === 'portfolio' && <PortfolioTab positions={realPositions.length > 0 ? realPositions : []} engineState={engineState} unrealizedPnl={realPnl} cumulativePnl={cumulativePnl} equity={equity} hasRealData={realPositions.length > 0} hasCumulative={hasCumulativePnl} botRunning={botRunning} onToggleBot={handleToggleBot} botBusy={botBusy} />"
)

open('website-frontend/src/App.jsx', 'w', encoding='utf-8').write(content3)
print('Done - App.jsx patched successfully')
