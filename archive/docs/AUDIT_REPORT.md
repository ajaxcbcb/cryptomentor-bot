# System Audit Report

**Generated:** 2026-04-04 14:45:00.491093

## Summary

- 🔴 Errors: 0
- 🟡 Warnings: 29
- ℹ️  Info: 30
- Total Issues: 59

## Detailed Findings

### WARNING: Database Operations
**File:** `Bismillah/bot.py:488`

Database operation without try-except block

---

### WARNING: Error Handling
**File:** `Bismillah/app/handlers_autotrade.py:882`

Function 'callback_setup_key' performs critical operations without try-except

---

### WARNING: Error Handling
**File:** `Bismillah/app/handlers_autotrade.py:1194`

Function '_show_leverage_preview' performs critical operations without try-except

---

### WARNING: Error Handling
**File:** `Bismillah/app/handlers_autotrade.py:1738`

Function 'callback_howto' performs critical operations without try-except

---

### WARNING: Error Handling
**File:** `Bismillah/app/handlers_autotrade.py:1775`

Function 'callback_delete_key' performs critical operations without try-except

---

### WARNING: Error Handling
**File:** `Bismillah/app/handlers_autotrade.py:1789`

Function 'callback_confirm_delete' performs critical operations without try-except

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_autotrade.py:1954`

Callback 'callback_uid_acc' might not answer the query (causes loading spinner)

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_autotrade.py:2017`

Callback 'callback_uid_reject' might not answer the query (causes loading spinner)

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:71`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:71`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:77`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:96`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:96`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:110`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:126`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:126`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:131`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:135`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_autotrade.py:844`

Database operation without try-except block

---

### INFO: User Notifications
**File:** `Bismillah/app/handlers_autotrade.py:1985`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/handlers_autotrade.py:2000`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/handlers_autotrade.py:2039`

send_message without error handling (user might not get notified of failures)

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_community.py:375`

Callback 'callback_community_acc' might not answer the query (causes loading spinner)

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_community.py:426`

Callback 'callback_community_reject' might not answer the query (causes loading spinner)

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_community.py:460`

Callback 'callback_community_member_acc' might not answer the query (causes loading spinner)

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_community.py:527`

Callback 'callback_community_member_reject' might not answer the query (causes loading spinner)

---

### WARNING: Database Operations
**File:** `Bismillah/app/handlers_community.py:326`

Database operation without try-except block

---

### INFO: User Notifications
**File:** `Bismillah/app/handlers_community.py:407`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/handlers_community.py:499`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/handlers_community.py:512`

send_message without error handling (user might not get notified of failures)

---

### WARNING: Callback Handling
**File:** `Bismillah/app/handlers_skills.py:152`

Callback 'callback_skill_nocredits' might not answer the query (causes loading spinner)

---

### WARNING: Database Operations
**File:** `Bismillah/app/autotrade_engine.py:755`

Database operation without try-except block

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:870`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:905`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:932`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1032`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1110`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1163`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1188`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1255`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1273`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1465`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1498`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1526`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1538`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1551`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1565`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/autotrade_engine.py:1660`

send_message without error handling (user might not get notified of failures)

---

### WARNING: Database Operations
**File:** `Bismillah/app/scalping_engine.py:491`

Database operation without try-except block

---

### WARNING: Database Operations
**File:** `Bismillah/app/scalping_engine.py:935`

Database operation without try-except block

---

### INFO: User Notifications
**File:** `Bismillah/app/scalping_engine.py:65`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/scalping_engine.py:959`

send_message without error handling (user might not get notified of failures)

---

### WARNING: Database Operations
**File:** `Bismillah/app/scheduler.py:448`

Database operation without try-except block

---

### INFO: User Notifications
**File:** `Bismillah/app/scheduler.py:262`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/scheduler.py:327`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/scheduler.py:350`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/scheduler.py:483`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/scheduler.py:518`

send_message without error handling (user might not get notified of failures)

---

### INFO: User Notifications
**File:** `Bismillah/app/scheduler.py:622`

send_message without error handling (user might not get notified of failures)

---

