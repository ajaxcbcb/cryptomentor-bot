#!/usr/bin/env python3
content = open('website-frontend/src/App.jsx', 'r', encoding='utf-8').read()
lines = content.split('\n')

new_block = r"""function PortfolioTab({ positions, engineState, unrealizedPnl, cumulativePnl, equity, hasRealData, hasCumulative, botRunning, onToggleBot }) {
  const pnlAbs = Math.abs(unrealizedPnl).toFixed(2);
  const pnlDisplay = hasRealData ? `${unrealizedPnl >= 0 ? '+' : '-'}$${pnlAbs}` : '$0.00';
  const realizedAbs = Math.abs(cumulativePnl).toFixed(2);
  const realizedDisplay = `${cumulativePnl >= 0 ? '+' : '-'}$${realizedAbs}`;
  const equityDisplay = equity !== null && equity !== undefined ? `$${Number(equity).toFixed(2)}` : '—';

  return (
    <div className="max-w-6xl mx-auto space-y-6 md:space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 fill-mode-both">
      <header className="mb-8 md:mb-12 flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div><h2 className="text-3xl md:text-5xl font-black text-white mb-2 tracking-tighter">Portfolio Status</h2><span className="text-slate-400 font-medium text-sm md:text-lg">AI-managed assets overview.</span></div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 bg-white/5 border border-white/10 px-4 py-2.5 rounded-xl backdrop-blur-md">
            <div className="flex flex-col items-end border-r border-white/10 pr-3"><span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest mb-0.5">Mode</span><span className={`text-xs font-black uppercase tracking-wider ${engineState.tradingMode === 'scalping' ? 'text-fuchsia-400' : 'text-cyan-400'}`}>{engineState.tradingMode}</span></div>
            <div className="flex items-center gap-2"><span className="relative flex h-2.5 w-2.5"><span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${botRunning ? 'bg-lime-400' : 'bg-slate-600'}`}></span><span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${botRunning ? 'bg-lime-400 shadow-[0_0_10px_rgba(163,230,53,0.8)]' : 'bg-slate-600'}`}></span></span><span className={`text-[10px] font-bold tracking-[0.1em] uppercase ${botRunning ? 'text-lime-400' : 'text-slate-500'}`}>{botRunning ? 'Active' : 'Stopped'}</span></div>
          </div>
          <button onClick={onToggleBot} className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm transition-all whitespace-nowrap ${botRunning ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25' : 'bg-lime-500/15 text-lime-400 border border-lime-500/30 hover:bg-lime-500/25'}`}>{botRunning ? <><StopCircle size={15} /> Stop Engine</> : <><Power size={15} /> Start Engine</>}</button>
        </div>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <StatCard title="Account Equity" value={equityDisplay} subtext="Avail + Margin + uPnL" icon={<Wallet className="text-cyan-400 w-6 h-6" />} glowColor="cyan" />
        <StatCard title="Unrealized PnL" value={pnlDisplay} subtext="Live open positions" isPositive={unrealizedPnl >= 0} icon={<Activity className={`w-6 h-6 ${unrealizedPnl >= 0 ? 'text-lime-400' : 'text-rose-400'}`} />} glowColor={unrealizedPnl >= 0 ? 'lime' : 'rose'} />
        <StatCard title="Realized PnL (30d)" value={realizedDisplay} subtext="Closed trades" isPositive={cumulativePnl >= 0} icon={<TrendingUp className="text-fuchsia-400 w-6 h-6" />} glowColor="fuchsia" />
        <StatCard title="Open Positions" value={positions.length.toString()} icon={<Target className="text-cyan-400 w-6 h-6" />} glowColor="cyan" />
      </div>"""

# Replace lines 374-396 (0-indexed)
lines[374:397] = new_block.split('\n')
open('website-frontend/src/App.jsx', 'w', encoding='utf-8').write('\n'.join(lines))
print('Done')
