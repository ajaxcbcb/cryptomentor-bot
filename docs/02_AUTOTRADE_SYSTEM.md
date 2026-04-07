# AutoTrade System - Complete Documentation

**Status:** ✅ Production  
**Last Updated:** April 7, 2026

---

## 🎯 Overview

AutoTrade adalah sistem copy trading otomatis yang:
- Menganalisis market 24/7
- Generate trading signals
- Execute trades otomatis
- Manage TP/SL dengan StackMentor
- Auto-switch mode berdasarkan market sentiment

---

## 🔄 Trading Modes

### 1. SCALPING Mode (5M)
**Best For:** Sideways/ranging markets

**Features:**
- Timeframe: 5 minutes
- StackMentor 3-tier TP (60%/30%/10%)
- Max hold time: 30 minutes
- Max risk: 5% per trade (safety cap)
- Max leverage: 10x (safety cap)
- Scan interval: 15 seconds

**TP Strategy:**
- TP1: 60% @ R:R 1:2
- TP2: 30% @ R:R 1:3
- TP3: 10% @ R:R 1:10
- Auto-breakeven: SL moves to entry when TP1 hit

**Safety Features:**
- Emergency close if SL setup fails
- Position size cap at 50% of balance
- Fallback to 2% risk if calculation fails

### 2. SWING Mode (15M)
**Best For:** Trending markets

**Features:**
- Timeframe: 15 minutes
- StackMentor 3-tier TP (60%/30%/10%)
- No max hold time
- User-defined risk %
- User-defined leverage
- Scan interval: 45 seconds

**TP Strategy:**
- Same as Scalping (StackMentor)
- TP1: 60% @ R:R 1:2
- TP2: 30% @ R:R 1:3
- TP3: 10% @ R:R 1:10

**Additional Features:**
- BTC bias filter (40% threshold)
- Multi-timeframe confluence
- SMC (Smart Money Concepts)
- 13 trading pairs

---

## 🤖 Auto Mode Switching

**File:** `app/auto_mode_switcher.py`

**How It Works:**
1. Runs every 15 minutes (background task)
2. Analyzes BTC market sentiment
3. Detects: SIDEWAYS, TRENDING, or VOLATILE
4. Auto-switches all users to optimal mode
5. Sends notification to users

**Market Detection:**
- ADX (trend strength)
- Bollinger Band Width (volatility)
- ATR (average true range)
- Price range analysis

**Decision Logic:**
- SIDEWAYS → Switch to SCALPING
- TRENDING → Switch to SWING
- VOLATILE (50% area) → Default to SCALPING

**Confidence Threshold:** 50% (aggressive switching)

---

## 📊 StackMentor System

**File:** `app/stackmentor.py`

**Purpose:** 3-tier TP system untuk maximize profit

**How It Works:**
1. Calculate 3 TP levels based on entry & SL
2. Split position into 60%/30%/10%
3. Set TP orders for each split
4. Monitor for TP hits
5. Auto-move SL to breakeven when TP1 hit

**Benefits:**
- Secure early profit (60% at TP1)
- Risk-free after TP1 (breakeven)
- Capture extended moves (TP2)
- Capture moonshots (TP3)

**Database:** `tp_partial_tracking` table

---

