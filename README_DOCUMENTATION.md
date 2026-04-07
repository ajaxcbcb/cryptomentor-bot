# CryptoMentor - Documentation Index

**Last Updated:** April 7, 2026  
**Version:** 2.0  
**Status:** ✅ Production

---

## 📚 Documentation Overview

Dokumentasi lengkap sistem CryptoMentor, termasuk Bismillah Bot, Whitelabel System, License Server, dan AutoTrade System.

---

## 🗂️ Documentation Files

### 1. Complete System Documentation
**File:** `COMPLETE_SYSTEM_DOCUMENTATION.md`

**Contents:**
- System overview
- Architecture diagram
- Bismillah Bot overview
- Whitelabel system
- License server
- Database schema
- Deployment guide
- Monitoring & troubleshooting

**Use Case:** Comprehensive reference untuk seluruh sistem

---

### 2. AutoTrade System
**File:** `docs/02_AUTOTRADE_SYSTEM.md`

**Contents:**
- Trading modes (Scalping & Swing)
- Auto mode switching
- StackMentor 3-tier TP
- Risk management
- Safety features

**Use Case:** Deep dive into AutoTrade functionality

---

### 3. StackMentor Integration
**File:** `SCALPING_STACKMENTOR_INTEGRATION.md`

**Contents:**
- Implementation details
- Code changes
- Benefits & features
- Testing checklist
- Deployment guide

**Use Case:** Technical documentation untuk StackMentor integration

---

### 4. Deployment Guide
**File:** `DEPLOY_SCALPING_STACKMENTOR.md`

**Contents:**
- Deployment commands
- Verification steps
- Monitoring guide
- Rollback plan

**Use Case:** Step-by-step deployment instructions

---

### 5. Deployment Success Report
**File:** `DEPLOYMENT_SUCCESS_STACKMENTOR.md`

**Contents:**
- Deployment summary
- Service status
- Verification results
- Next steps

**Use Case:** Post-deployment verification

---

### 6. Verification Checklist
**File:** `VERIFICATION_CHECKLIST.md`

**Contents:**
- Code verification
- Functional testing
- Database checks
- Monitoring commands

**Use Case:** Quality assurance checklist

---

### 7. All Users Verification
**File:** `VERIFICATION_ALL_USERS_STACKMENTOR.md`

**Contents:**
- User-specific condition checks
- Code flow analysis
- Testing plan
- Monitoring commands

**Use Case:** Ensure StackMentor applies to ALL users

---

### 8. Quick Reference Guide
**File:** `QUICK_REFERENCE_GUIDE.md`

**Contents:**
- System overview
- Trading modes comparison
- User notifications
- Configuration
- Troubleshooting

**Use Case:** Quick lookup reference

---

### 9. System Status
**File:** `SYSTEM_STATUS_CURRENT.md`

**Contents:**
- Current features
- Configuration
- Deployment status
- Verification checklist

**Use Case:** Current system state snapshot

---

## 🎯 Quick Navigation

### For Developers:
1. Start with: `COMPLETE_SYSTEM_DOCUMENTATION.md`
2. Deep dive: `docs/02_AUTOTRADE_SYSTEM.md`
3. Technical: `SCALPING_STACKMENTOR_INTEGRATION.md`

### For Deployment:
1. Read: `DEPLOY_SCALPING_STACKMENTOR.md`
2. Execute: Deployment commands
3. Verify: `VERIFICATION_CHECKLIST.md`
4. Check: `DEPLOYMENT_SUCCESS_STACKMENTOR.md`

### For Troubleshooting:
1. Check: `COMPLETE_SYSTEM_DOCUMENTATION.md` (Troubleshooting section)
2. Reference: `QUICK_REFERENCE_GUIDE.md`
3. Verify: `VERIFICATION_CHECKLIST.md`

### For Understanding Features:
1. Overview: `SYSTEM_STATUS_CURRENT.md`
2. Details: `docs/02_AUTOTRADE_SYSTEM.md`
3. User Guide: `QUICK_REFERENCE_GUIDE.md`

---

## 📊 System Components

### 1. Bismillah Bot (Main)
- **Path:** `Bismillah/`
- **Purpose:** Main trading bot
- **Features:** AutoTrade, Signals, Education
- **Documentation:** `COMPLETE_SYSTEM_DOCUMENTATION.md`

### 2. Whitelabel System
- **Path:** `Whitelabel #1/`
- **Purpose:** White-label solution
- **Features:** Custom branding, License-based
- **Documentation:** `COMPLETE_SYSTEM_DOCUMENTATION.md`

### 3. License Server
- **Path:** `license_server/`
- **Purpose:** License management
- **Features:** Validation, Billing, Monitoring
- **Documentation:** `COMPLETE_SYSTEM_DOCUMENTATION.md`

### 4. AutoTrade System
- **Files:** `app/autotrade_engine.py`, `app/scalping_engine.py`
- **Purpose:** Automated trading
- **Features:** 2 modes, StackMentor, Auto-switching
- **Documentation:** `docs/02_AUTOTRADE_SYSTEM.md`

---

## 🚀 Latest Updates

### April 7, 2026 - StackMentor Integration
**Status:** ✅ Deployed

**Changes:**
- Scalping mode now uses StackMentor 3-tier TP
- Auto-breakeven when TP1 hit
- Emergency close if SL fails
- New notification format

**Documentation:**
- `SCALPING_STACKMENTOR_INTEGRATION.md`
- `DEPLOYMENT_SUCCESS_STACKMENTOR.md`

---

## 📞 Support

### Documentation Issues
If you find any issues with documentation:
1. Check the specific file for details
2. Review related files for context
3. Check deployment logs for errors

### System Issues
If you encounter system issues:
1. Check: `COMPLETE_SYSTEM_DOCUMENTATION.md` (Troubleshooting)
2. Review: Service logs
3. Verify: Configuration files

---

## 🔗 Related Files

### Configuration
- `Bismillah/.env` - Main bot configuration
- `Whitelabel #1/.env` - Whitelabel configuration
- `license_server/.env` - License server configuration

### Database
- `db/setup_supabase.sql` - Main database schema
- `db/add_auto_mode_switcher.sql` - Auto mode switcher
- `db/add_tp_partial_tracking.sql` - StackMentor tracking

### Deployment
- `fix_autotrade_error.sh` - Deployment script
- Service file: `/etc/systemd/system/cryptomentor.service`

---

**Maintained By:** Development Team  
**Last Review:** April 7, 2026  
**Next Review:** Monitor for 24 hours, update based on feedback
