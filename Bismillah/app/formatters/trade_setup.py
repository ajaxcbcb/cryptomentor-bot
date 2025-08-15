
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple

def _fmt_price(v: float | int | str, prec: int = 2) -> str:
    try:
        x = float(v)
    except Exception:
        return str(v)
    # Trim desimal tak perlu (2–6 digit dinamis)
    s = f"{x:,.6f}"
    # potong trailing nol & titik
    while s and s[-1] == "0":
        s = s[:-1]
    if s and s[-1] == ".":
        s = s[:-1]
    return f"${s}"

def _single_entry(entry: Optional[float], entry_zone: Optional[Tuple[float, float]]) -> Optional[float]:
    """
    Prioritas:
    1) 'entry' (optimal_entry) jika ada
    2) midpoint dari entry_zone
    3) None
    """
    if entry is not None:
        return float(entry)
    if entry_zone and len(entry_zone) == 2:
        lo, hi = float(entry_zone[0]), float(entry_zone[1])
        return (lo + hi) / 2.0
    return None

def format_detailed_setup(
    setup: Dict[str, Any],
    *,
    title: str = "💰 DETAILED TRADING SETUP",
    show_zone_line: bool = False,  # default: sembunyikan range
) -> str:
    """
    Input 'setup' bisa berisi:
      {
        "entry": float | None,                # optimal entry (opsional)
        "entry_zone": (low, high) | None,     # range (opsional)
        "stop": float,
        "tp1": float, "tp1_pct": 50,          # opsional tp*_pct hanya teks
        "tp2": float, "tp2_pct": 30,
        "tp3": float, "tp3_pct": 20,
        "rr": float,                          # risk/reward
        "max_risk_pct": float,                # contoh 2.5
      }
    """
    entry_val = _single_entry(setup.get("entry"), setup.get("entry_zone"))
    stop = setup.get("stop")
    tp1, tp2, tp3 = setup.get("tp1"), setup.get("tp2"), setup.get("tp3")
    rr = setup.get("rr")
    max_risk = setup.get("max_risk_pct")

    lines = [title]

    # (Opsional) tampilkan zona sebagai info text, bukan utama
    if show_zone_line and isinstance(setup.get("entry_zone"), (list, tuple)) and len(setup["entry_zone"]) == 2:
        lo, hi = setup["entry_zone"]
        lines.append(f"• Zone Info: {_fmt_price(lo)} – {_fmt_price(hi)}")

    # 🔹 Satu titik Entry
    if entry_val is not None:
        lines.append(f"• 🎯 Entry: {_fmt_price(entry_val)}")

    # 🛑 Stop Loss
    if stop is not None:
        lines.append(f"• 🛑 Stop Loss: {_fmt_price(stop)}")

    # 🎯 Take Profits
    if tp1 is not None:
        pct = setup.get("tp1_pct")
        suffix = f" ({pct}%)" if pct is not None else ""
        lines.append(f"• 1️⃣ TP1: {_fmt_price(tp1)}{suffix}")
    if tp2 is not None:
        pct = setup.get("tp2_pct")
        suffix = f" ({pct}%)" if pct is not None else ""
        lines.append(f"• 2️⃣ TP2: {_fmt_price(tp2)}{suffix}")
    if tp3 is not None:
        pct = setup.get("tp3_pct")
        suffix = f" ({pct}%)" if pct is not None else ""
        lines.append(f"• 3️⃣ TP3: {_fmt_price(tp3)}{suffix}")

    # ⚖️ Risk/Reward
    if rr is not None:
        # tampilkan 1 desimal maksimum
        try:
            rr_val = float(rr)
            rr_txt = f"{rr_val:.1f}".rstrip("0").rstrip(".")
        except Exception:
            rr_txt = str(rr)
        lines.append(f"• ⚖️ Risk/Reward: {rr_txt}:1")

    # 📉 Max Risk
    if max_risk is not None:
        try:
            mr = float(max_risk)
            mr_txt = f"{mr:.2f}".rstrip("0").rstrip(".")
        except Exception:
            mr_txt = str(max_risk)
        lines.append(f"• 📉 Max Risk: {mr_txt}% per position")

    # ⛔️ Pastikan tidak dibungkus code block
    return "\n".join(lines)
