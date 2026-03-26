# Implementation Plan: Automaton Integration

## Overview

This implementation plan breaks down the Automaton integration into discrete, incremental tasks following a phased approach: database setup → wallet management → Conway API integration → deposit monitoring → agent management → revenue collection → UI integration → background services → hardening. Each task builds on previous work and includes property-based testing to validate correctness across all inputs.

**Implementation Language:** Python 3.x with python-telegram-bot library

**Implementation Status:** Core infrastructure and business logic complete. Background services operational. Property-based testing in progress (5/55 complete).

## Tasks

- [x] 1. Database Schema and Infrastructure Setup
  - Create all required database tables in Supabase (custodial_wallets, wallet_deposits, wallet_withdrawals, user_automatons, automaton_transactions, platform_revenue)
  - Add indexes for performance optimization (wallet_address, user_id, tx_hash, status, timestamp)
  - Set up environment variables in Railway (WALLET_ENCRYPTION_KEY, POLYGON_RPC_URL, CONWAY_API_KEY)
  - Configure Polygon RPC connection with Web3.py
  - Verify database connectivity and table creation
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1_

- [x] 2. Wallet Manager Implementation
  - [x] 2.1 Create `app/wallet_manager.py` with WalletManager class
    - Implement Fernet encryption initialization with master key from environment
    - Implement create_custodial_wallet method (generate Ethereum wallet, encrypt private key, store in database)
    - Implement get_user_wallet method (retrieve wallet from database by user_id)
    - Implement decrypt_private_key method (decrypt for transaction signing, admin only)
    - Implement get_wallet_balance method (query blockchain for USDT/USDC balance)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 11.1, 11.2, 11.3_
  
  - [x] 2.2 Write property test for unique wallet generation
    - **Property 1: Unique Wallet Generation**
    - **Validates: Requirements 1.1**
  
  - [x] 2.3 Write property test for encryption round trip
    - **Property 2: Wallet Encryption Round Trip**
    - **Validates: Requirements 1.2, 11.1**
  
  - [x] 2.4 Write property test for one wallet per user invariant
    - **Property 3: One Wallet Per User Invariant**
    - **Validates: Requirements 1.4**
  
  - [x] 2.5 Write property test for audit logging
    - **Property 27: Audit Logging for Decryption**
    - **Validates: Requirements 11.4**


- [x] 3. Conway API Integration
  - [x] 3.1 Create `app/conway_integration.py` with ConwayIntegration class
    - Implement fund_agent method (POST /credits/transfer with agent_wallet and amount)
    - Implement check_agent_balance method (GET /credits/balance with agent_wallet)
    - Implement spawn_agent_runtime method (POST /agents/spawn with agent config)
    - Implement get_agent_logs method (GET /agents/{wallet}/logs)
    - Implement retry logic with exponential backoff (1s, 2s, 4s for 3 attempts)
    - Implement Bearer token authentication with CONWAY_API_KEY
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [x] 3.2 Create test script `test_conway_api.py`
    - Test health check endpoint connectivity
    - Test deposit address generation
    - Test credit balance retrieval
    - Test agent spawning
    - Test agent status retrieval
    - Test transaction history
    - _Requirements: 13.1, 13.2, 13.3_
  
  - [x] 3.3 Write property test for Conway API credit transfer
    - **Property 33: Conway API Credit Transfer**
    - **Validates: Requirements 13.1**
  
  - [-] 3.4 Write property test for Conway API balance check
    - **Property 34: Conway API Balance Check**
    - **Validates: Requirements 13.2**
  
  - [ ] 3.5 Write property test for Conway API authentication
    - **Property 35: Conway API Authentication**
    - **Validates: Requirements 13.3**
  
  - [ ] 3.6 Write property test for API retry logic
    - **Property 36: API Retry Logic**
    - **Validates: Requirements 13.4, 23.5**
  
  - [ ] 3.7 Write unit test for API failure notification
    - **Property 37: API Failure Notification**
    - **Validates: Requirements 13.5**

- [x] 4. Deposit Monitor Service
  - [x] 4.1 Create `app/deposit_monitor.py` with DepositMonitor class
    - Implement Web3 connection to Polygon network
    - Implement ERC20 contract interaction for USDT (0xc2132D05D31c914a87C6611C10748AEb04B58e8F)
    - Implement ERC20 contract interaction for USDC (0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174)
    - Implement balance checking for all custodial wallets (30 second interval)
    - Implement deposit detection and confirmation tracking (12 blocks)
    - _Requirements: 2.1, 2.2, 2.3, 15.2, 15.3, 15.4, 15.5_
  
  - [x] 4.2 Implement deposit processing logic
    - Calculate 2% platform fee (deduct before conversion)
    - Convert to Conway credits at 1 USDT = 100 credits, 1 USDC = 100 credits
    - Update custodial_wallets balance (balance_usdt, balance_usdc, conway_credits)
    - Record in wallet_deposits table (tx_hash, amount, token, network, status, confirmations)
    - Credit Conway credits via Conway API
    - Send Telegram notification to user
    - _Requirements: 2.4, 2.6, 3.1, 3.2, 3.3, 3.5_
  
  - [x] 4.3 Write property test for deposit detection and recording
    - **Property 5: Deposit Detection and Recording**
    - **Validates: Requirements 2.2**
  
  - [ ] 4.4 Write property test for confirmation status transition
    - **Property 6: Confirmation Status Transition**
    - **Validates: Requirements 2.3, 15.5**
  
  - [x] 4.5 Write property test for Conway credits conversion formula
    - **Property 7: Conway Credits Conversion Formula**
    - **Validates: Requirements 2.4, 3.1, 3.2, 3.3, 21.1**
  
  - [x] 4.6 Write property test for minimum deposit validation
    - **Property 8: Minimum Deposit Validation**
    - **Validates: Requirements 3.4**
  
  - [ ] 4.7 Write property test for ERC20 balance query
    - **Property 38: ERC20 Balance Query**
    - **Validates: Requirements 15.4**
  
  - [ ] 4.8 Write property test for deposit confirmation notification
    - **Property 44: Deposit Confirmation Notification**
    - **Validates: Requirements 20.1**

- [x] 5. Checkpoint - Core Infrastructure Complete
  - Ensure all tests pass
  - Verify database tables created with proper indexes
  - Verify wallet generation works (unique addresses, encryption)
  - Verify Conway API integration works (fund, balance check)
  - Verify deposit detection works on testnet
  - Ask the user if questions arise


- [x] 6. Automaton Manager Implementation
  - [x] 6.1 Create `app/automaton_manager.py` with AutomatonManager class
    - Implement spawn_agent method with premium verification (query users.is_premium)
    - Implement credit balance verification (check users.credits >= 100,000)
    - Implement credit deduction (deduct exactly 100,000 credits)
    - Implement agent wallet generation (unique Ethereum address)
    - Implement Conway API key provisioning
    - Implement Railway deployment with genesis prompt
    - Implement database registration in user_automatons table
    - Implement spawn confirmation notification
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 17.1, 17.2, 18.1, 18.2, 18.3, 18.4_
  
  - [x] 6.2 Implement agent status tracking
    - Implement get_agent_status method (retrieve from user_automatons)
    - Implement calculate_survival_tier method (normal >= 5000, low_compute >= 1000, critical > 0, dead = 0)
    - Implement runtime estimation (credits / consumption_rate by tier)
    - Implement transaction aggregation (sum earnings, sum expenses)
    - Implement stop_agent method (update status to 'paused')
    - Implement restart_agent method (verify credits > 0, update status to 'active')
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 16.1, 16.2, 16.3, 16.4, 16.5_
  
  - [ ] 6.3 Write property test for premium access control
    - **Property 9: Premium Access Control for Spawning**
    - **Validates: Requirements 4.1, 17.2**
  
  - [ ] 6.4 Write property test for spawn credit validation
    - **Property 10: Spawn Credit Balance Validation**
    - **Validates: Requirements 4.2, 18.2**
  
  - [ ] 6.5 Write property test for spawn fee deduction
    - **Property 11: Spawn Fee Deduction**
    - **Validates: Requirements 4.3, 18.3**
  
  - [ ] 6.6 Write property test for agent wallet uniqueness
    - **Property 12: Agent Wallet Uniqueness**
    - **Validates: Requirements 4.4**
  
  - [ ] 6.7 Write property test for spawn confirmation notification
    - **Property 13: Spawn Confirmation Notification**
    - **Validates: Requirements 4.8, 20.2**
  
  - [ ] 6.8 Write property test for agent status retrieval
    - **Property 14: Agent Status Retrieval**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ] 6.9 Write property test for survival tier classification
    - **Property 15: Survival Tier Classification**
    - **Validates: Requirements 5.3, 16.1, 16.2, 16.3, 16.4**
  
  - [ ] 6.10 Write property test for runtime estimation
    - **Property 16: Runtime Estimation**
    - **Validates: Requirements 5.4**
  
  - [ ] 6.11 Write property test for transaction aggregation
    - **Property 17: Transaction Aggregation**
    - **Validates: Requirements 5.5, 22.3, 22.4**
  
  - [ ] 6.12 Write property test for dead agent operation prevention
    - **Property 39: Dead Agent Operation Prevention**
    - **Validates: Requirements 16.5**
  
  - [ ] 6.13 Write property test for premium status query
    - **Property 40: Premium Status Query**
    - **Validates: Requirements 17.1, 18.1**
  
  - [ ] 6.14 Write property test for expired premium agent persistence
    - **Property 41: Expired Premium Agent Persistence**
    - **Validates: Requirements 17.4, 17.5**
  
  - [ ] 6.15 Write property test for spawn activity logging
    - **Property 42: Spawn Activity Logging**
    - **Validates: Requirements 18.4**
  
  - [ ] 6.16 Write property test for spawn failure refund
    - **Property 43: Spawn Failure Refund**
    - **Validates: Requirements 18.5**

- [x] 7. Balance Monitor Service
  - [x] 7.1 Create `app/balance_monitor.py` with BalanceMonitor class
    - Implement hourly balance checking for all active agents
    - Implement low balance alert logic (< 5000 credits, warning)
    - Implement critical balance alert logic (< 1000 credits, critical)
    - Implement runtime estimation by tier (normal: 200/day, low_compute: 100/day, critical: 50/day)
    - Implement send_low_balance_alert method (Telegram notification with balance, runtime, deposit instructions)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 7.2 Write property test for low balance warning trigger
    - **Property 18: Low Balance Warning Trigger**
    - **Validates: Requirements 6.3, 20.3**
  
  - [ ] 7.3 Write property test for critical balance alert trigger
    - **Property 19: Critical Balance Alert Trigger**
    - **Validates: Requirements 6.2, 20.4**
  
  - [ ] 7.4 Write property test for alert message completeness
    - **Property 20: Alert Message Completeness**
    - **Validates: Requirements 6.4, 6.5**
  
  - [ ] 7.5 Write property test for dead agent notification
    - **Property 45: Dead Agent Notification**
    - **Validates: Requirements 20.5**


- [x] 8. Revenue Manager Implementation
  - [x] 8.1 Create `app/revenue_manager.py` with RevenueManager class
    - Implement calculate_deposit_fee method (2% of deposit amount)
    - Implement collect_performance_fee method (20% of realized profits)
    - Implement fee collection from agent credits (transfer via Conway API)
    - Implement platform_revenue table updates (record source, amount, agent_id, timestamp)
    - Implement record_platform_fee method (insert into platform_revenue)
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 23.1, 23.2, 23.3, 23.4_
  
  - [x] 8.2 Implement revenue reporting
    - Implement get_revenue_report method (aggregate by period: daily/weekly/monthly)
    - Implement time-based aggregation (group by timestamp within period)
    - Implement source-based aggregation (group by deposit_fee, performance_fee, withdrawal_fee)
    - Implement top agents ranking (sum revenue by agent_id, sort descending, limit 10)
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_
  
  - [ ] 8.3 Write property test for performance fee calculation
    - **Property 46: Performance Fee Calculation**
    - **Validates: Requirements 21.2, 21.3, 23.1**
  
  - [ ] 8.4 Write property test for performance fee transaction logging
    - **Property 47: Performance Fee Transaction Logging**
    - **Validates: Requirements 21.4, 21.5, 23.4**
  
  - [ ] 8.5 Write property test for performance fee balance transfer
    - **Property 48: Performance Fee Balance Transfer**
    - **Validates: Requirements 23.2**
  
  - [ ] 8.6 Write property test for profit transaction recording
    - **Property 49: Profit Transaction Recording**
    - **Validates: Requirements 22.1**
  
  - [ ] 8.7 Write property test for loss transaction recording
    - **Property 50: Loss Transaction Recording**
    - **Validates: Requirements 22.2**
  
  - [ ] 8.8 Write property test for net profit calculation
    - **Property 51: Net Profit Calculation**
    - **Validates: Requirements 22.5**
  
  - [ ] 8.9 Write property test for revenue report aggregation
    - **Property 52: Revenue Report Aggregation**
    - **Validates: Requirements 24.1, 24.2**
  
  - [ ] 8.10 Write property test for time-based revenue breakdown
    - **Property 53: Time-Based Revenue Breakdown**
    - **Validates: Requirements 24.3**
  
  - [ ] 8.11 Write property test for revenue source breakdown
    - **Property 54: Revenue Source Breakdown**
    - **Validates: Requirements 24.4**
  
  - [ ] 8.12 Write property test for top revenue agents
    - **Property 55: Top Revenue Agents**
    - **Validates: Requirements 24.5**

- [x] 9. Checkpoint - Core Business Logic Complete
  - Ensure all tests pass (unit + property tests completed so far)
  - Verify agent spawning works end-to-end (premium check, credit deduction, wallet generation, deployment)
  - Verify balance monitoring works (hourly checks, alerts sent)
  - Verify fee collection works (deposit fees, performance fees)
  - Ask the user if questions arise

- [x] 10. Telegram Bot Handlers
  - [x] 10.1 Create `app/handlers_automaton.py` with command handlers
    - Implement spawn_agent_command handler (verify premium, verify credits, confirm with user, execute spawn)
    - Implement agent_status_command handler (display name, wallet, credits, tier, runtime, earnings, expenses)
    - Implement deposit_command handler (show wallet address in monospace, generate QR code, list networks, show conversion rates)
    - Implement balance_command handler (show wallet address, USDT/USDC balances, Conway credits, total deposited/spent)
    - Implement agent_logs_command handler (retrieve last 20 transactions, format by type, show amounts with colors)
    - Implement withdraw_command handler (validate amount >= 10 USDT, check balance, create withdrawal request, deduct 1 USDT fee)
    - _Requirements: 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 9.4, 12.1, 12.2, 12.3, 12.4_
  
  - [ ] 10.2 Write property test for deposit address response completeness
    - **Property 4: Deposit Address Response Completeness**
    - **Validates: Requirements 1.5**
  
  - [ ] 10.3 Write property test for QR code generation
    - **Property 21: QR Code Generation**
    - **Validates: Requirements 8.2**
  
  - [ ] 10.4 Write property test for transaction log limiting
    - **Property 22: Transaction Log Limiting**
    - **Validates: Requirements 9.1**
  
  - [ ] 10.5 Write property test for transaction record completeness
    - **Property 23: Transaction Record Completeness**
    - **Validates: Requirements 9.2**
  
  - [ ] 10.6 Write unit tests for command handlers
    - Test spawn command with premium user (success case)
    - Test spawn command with non-premium user (rejection)
    - Test spawn command with insufficient credits (rejection)
    - Test deposit command QR code generation
    - Test balance command display format
    - Test agent logs pagination and formatting
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_


- [x] 11. Menu System Integration
  - [x] 11.1 Update `menu_system.py` to add AI Agent menu
    - Add "🤖 AI Agent" button to main menu
    - Create AI Agent submenu with options: Spawn Agent, Agent Status, Fund Agent, Agent Logs, Agent Settings
    - Wire submenu buttons to handlers (spawn_agent_command, agent_status_command, deposit_command, agent_logs_command)
    - _Requirements: 7.1, 7.2_
  
  - [x] 11.2 Update menu handlers to register automaton handlers
    - Register spawn_agent_command in bot application
    - Register agent_status_command in bot application
    - Register deposit_command in bot application
    - Register balance_command in bot application
    - Register agent_logs_command in bot application
    - _Requirements: 7.3, 7.4, 7.5_
  
  - [ ] 11.3 Write integration tests for menu navigation
    - Test main menu displays AI Agent button
    - Test AI Agent button shows submenu with all options
    - Test submenu buttons trigger correct handlers
    - Test menu navigation flow (main → AI Agent → specific action)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 12. Notification System
  - [x] 12.1 Create `app/notifications.py` with notification helpers
    - Implement send_deposit_confirmation (amount, token, credited Conway credits)
    - Implement send_spawn_confirmation (agent name, wallet, initial credits, status)
    - Implement send_low_balance_warning (balance, estimated runtime, deposit recommendation)
    - Implement send_critical_balance_alert (balance, runtime < 1 day, urgent deposit instructions)
    - Implement send_dead_agent_notification (agent name, status 'dead', funding required)
    - _Requirements: 2.6, 4.8, 6.4, 6.5, 20.1, 20.2, 20.3, 20.4, 20.5_

- [x] 13. Admin Dashboard Features
  - [x] 13.1 Create `app/handlers_admin_automaton.py` with admin commands
    - Implement /admin_wallets command (total wallets, total USDT/USDC, all-time deposits, all-time spending)
    - Implement /admin_wallet_details <user_id> command (specific wallet transaction history)
    - Implement /admin_revenue command (total deposit fees, total performance fees, daily/weekly/monthly breakdown)
    - Implement /admin_agents command (active agents count, survival rate percentage, agent statistics)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 24.1, 24.2, 24.3, 24.4, 24.5_
  
  - [ ] 13.2 Write property test for admin wallet aggregation
    - **Property 24: Admin Wallet Aggregation**
    - **Validates: Requirements 10.1**
  
  - [ ] 13.3 Write property test for platform revenue calculation
    - **Property 25: Platform Revenue Calculation**
    - **Validates: Requirements 10.3**
  
  - [ ] 13.4 Write property test for survival rate calculation
    - **Property 26: Survival Rate Calculation**
    - **Validates: Requirements 10.4**

- [x] 14. Background Services Setup
  - [x] 14.1 Create `app/background_services.py` with service orchestration
    - Implement async task for deposit monitor (30 second interval)
    - Implement async task for balance monitor (1 hour interval)
    - Implement async task for performance fee collector (5 minute interval)
    - Implement graceful shutdown handling (stop all tasks on SIGTERM/SIGINT)
    - Implement health check endpoint (verify all services running)
    - _Requirements: 2.1, 6.1_
  
  - [x] 14.2 Update `bot.py` to start background services
    - Start background services on bot startup (before polling)
    - Stop background services on bot shutdown (after polling stops)
    - Add error handling for service failures (restart with backoff)
    - Add logging for service status (started, stopped, errors)
    - _Requirements: 2.1, 6.1_

- [x] 15. Checkpoint - Full Feature Complete
  - Ensure all tests pass (unit + property tests completed)
  - Verify end-to-end spawn workflow (UI → verification → deployment → notification)
  - Verify end-to-end deposit workflow (blockchain → detection → conversion → notification)
  - Verify end-to-end fee collection (profit → calculation → transfer → recording)
  - Verify all notifications work (deposit, spawn, low balance, critical, dead)
  - Verify admin dashboard functional (wallets, revenue, agents)
  - Ask the user if questions arise

- [ ] 16. Withdrawal Processing
  - [x] 16.1 Implement withdrawal request handling
    - Validate withdrawal amount (minimum 10 USDT)
    - Validate user balance (balance_usdt >= amount)
    - Create withdrawal request in wallet_withdrawals table (status 'pending')
    - Deduct 1 USDT flat fee from withdrawal amount
    - Queue for admin processing (notify admin via Telegram)
    - _Requirements: 12.1, 12.2, 12.3, 12.4_
  
  - [x] 16.2 Implement admin withdrawal processing
    - Create /admin_process_withdrawal <withdrawal_id> command
    - Decrypt private key using wallet_manager (admin only)
    - Sign and broadcast transaction to Polygon network
    - Update withdrawal status to 'completed' in database
    - Record transaction hash in tx_hash field
    - Notify user of successful withdrawal
    - _Requirements: 12.5_
  
  - [-] 16.3 Write property test for withdrawal balance validation
    - **Property 28: Withdrawal Balance Validation**
    - **Validates: Requirements 12.1**
  
  - [ ] 16.4 Write property test for minimum withdrawal validation
    - **Property 29: Minimum Withdrawal Validation**
    - **Validates: Requirements 12.2**
  
  - [ ] 16.5 Write property test for withdrawal fee deduction
    - **Property 30: Withdrawal Fee Deduction**
    - **Validates: Requirements 12.3**
  
  - [ ] 16.6 Write property test for withdrawal request persistence
    - **Property 31: Withdrawal Request Persistence**
    - **Validates: Requirements 12.4**
  
  - [ ] 16.7 Write property test for withdrawal status transition
    - **Property 32: Withdrawal Status Transition**
    - **Validates: Requirements 12.5**


- [ ] 17. Security Hardening
  - [x] 17.1 Implement audit logging in `app/audit_logger.py`
    - Log all private key decryption events (timestamp, wallet_address, operation_type, admin_id)
    - Log all admin operations (command, parameters, admin_id, timestamp)
    - Log all fee collections (type, amount, agent_id, timestamp)
    - Log all withdrawal requests (user_id, amount, to_address, timestamp)
    - Store audit logs in separate audit_logs table
    - _Requirements: 11.4_
  
  - [x] 17.2 Implement rate limiting
    - Limit spawn operations to 1 per user per hour (prevent spam)
    - Limit withdrawal requests to 3 per user per day (prevent abuse)
    - Limit API calls with exponential backoff (prevent rate limit errors)
    - Store rate limit state in Redis or in-memory cache
    - _Requirements: 13.4_
  
  - [ ] 17.3 Add input validation
    - Validate Ethereum addresses using regex (^0x[a-fA-F0-9]{40}$)
    - Validate amounts (positive, within reasonable limits)
    - Sanitize user inputs (prevent SQL injection, XSS)
    - Validate token types (only USDT, USDC allowed)
    - Validate network types (only polygon, base, arbitrum allowed)
    - _Requirements: 12.4_
  
  - [ ] 17.4 Implement master key rotation
    - Create /admin_rotate_encryption_key command
    - Generate new Fernet key
    - Re-encrypt all private keys with new key
    - Update WALLET_ENCRYPTION_KEY in Railway
    - Verify all wallets can be decrypted with new key
    - _Requirements: 11.5_

- [x] 18. Error Handling and Recovery
  - [x] 18.1 Create `app/error_handler.py` with error handlers
    - Implement handle_wallet_generation_error (log, notify admin, return user-friendly message)
    - Implement handle_blockchain_error (retry with backoff, log, continue on next cycle)
    - Implement handle_conway_api_error (retry 3 times, log, notify admin after failures)
    - Implement handle_database_error (rollback transaction, log, return generic error)
    - Implement handle_deposit_processing_error (mark deposit as 'failed', log, notify user)
    - Implement handle_spawn_error (refund spawn fee, log, notify user with error details)
    - Implement handle_fee_collection_error (retry on next profit event, log, don't block agent)
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_
  
  - [x] 18.2 Implement error notification system
    - Send admin alerts for critical errors (wallet encryption key missing, database connection lost, Conway API auth failure)
    - Send user-friendly error messages (clear description, actionable steps, error ID for support)
    - Include error IDs for support reference (UUID for each error)
    - Implement error message formatting (emoji, bold headers, bullet points)
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 19. Documentation and Deployment
  - [ ] 19.1 Create deployment documentation
    - Document all environment variables (TELEGRAM_BOT_TOKEN, SUPABASE_URL, POLYGON_RPC_URL, WALLET_ENCRYPTION_KEY, CONWAY_API_KEY, ADMIN_IDS)
    - Document database migration steps (run migrations in order, verify table creation)
    - Document Railway deployment process (connect GitHub, set env vars, deploy)
    - Document monitoring setup (logs, metrics, alerts)
  
  - [ ] 19.2 Create user documentation
    - How to spawn an agent (premium required, 100k credits, genesis prompt)
    - How to deposit funds (get wallet address, send USDT/USDC on Polygon, wait for confirmation)
    - How to check agent status (view credits, tier, runtime, earnings)
    - How to withdraw funds (minimum 10 USDT, 1 USDT fee, admin processing)
    - FAQ section (common issues, troubleshooting, support contact)
  
  - [ ] 19.3 Deploy to Railway
    - Set up environment variables in Railway dashboard
    - Run database migrations (execute SQL scripts in Supabase)
    - Deploy bot with background services (push to GitHub, Railway auto-deploys)
    - Verify all services running (check logs, test commands)
    - Monitor logs for errors (watch for exceptions, API failures)

- [ ] 20. Final Checkpoint - Production Ready
  - All tests passing (100+ property test iterations per test)
  - All background services running (deposit monitor, balance monitor, fee collector)
  - All notifications working (deposit, spawn, low balance, critical, dead)
  - Admin dashboard functional (wallets, revenue, agents, withdrawals)
  - Documentation complete (deployment, user guide, FAQ)
  - Monitoring and alerting configured (logs, metrics, admin alerts)
  - Security audit passed (encryption, audit logging, rate limiting, input validation)
  - Ready for production launch

## Property-Based Test Summary

The following 55 correctness properties need property-based tests (marked with * in tasks above):

**Wallet & Encryption (Properties 1-4, 27):**
- [x] Property 1: Unique Wallet Generation (Task 2.2)
- [x] Property 2: Wallet Encryption Round Trip (Task 2.3)
- [x] Property 3: One Wallet Per User Invariant (Task 2.4)
- [ ] Property 4: Deposit Address Response Completeness (Task 10.2)
- [ ] Property 27: Audit Logging for Decryption (Task 2.5)

**Deposit Processing (Properties 5-8, 44):**
- [x] Property 5: Deposit Detection and Recording (Task 4.3)
- [ ] Property 6: Confirmation Status Transition (Task 4.4)
- [x] Property 7: Conway Credits Conversion Formula (Task 4.5)
- [x] Property 8: Minimum Deposit Validation (Task 4.6)
- [ ] Property 44: Deposit Confirmation Notification (Task 4.8)

**Agent Spawning (Properties 9-13, 40-43):**
- [ ] Property 9: Premium Access Control for Spawning (Task 6.3)
- [ ] Property 10: Spawn Credit Balance Validation (Task 6.4)
- [ ] Property 11: Spawn Fee Deduction (Task 6.5)
- [ ] Property 12: Agent Wallet Uniqueness (Task 6.6)
- [ ] Property 13: Spawn Confirmation Notification (Task 6.7)
- [ ] Property 40: Premium Status Query (Task 6.13)
- [ ] Property 41: Expired Premium Agent Persistence (Task 6.14)
- [ ] Property 42: Spawn Activity Logging (Task 6.15)
- [ ] Property 43: Spawn Failure Refund (Task 6.16)

**Agent Status (Properties 14-17, 39):**
- [ ] Property 14: Agent Status Retrieval (Task 6.8)
- [ ] Property 15: Survival Tier Classification (Task 6.9)
- [ ] Property 16: Runtime Estimation (Task 6.10)
- [ ] Property 17: Transaction Aggregation (Task 6.11)
- [ ] Property 39: Dead Agent Operation Prevention (Task 6.12)

**Balance Monitoring (Properties 18-20, 45):**
- [ ] Property 18: Low Balance Warning Trigger (Task 7.2)
- [ ] Property 19: Critical Balance Alert Trigger (Task 7.3)
- [ ] Property 20: Alert Message Completeness (Task 7.4)
- [ ] Property 45: Dead Agent Notification (Task 7.5)

**UI & Display (Properties 21-23):**
- [ ] Property 21: QR Code Generation (Task 10.3)
- [ ] Property 22: Transaction Log Limiting (Task 10.4)
- [ ] Property 23: Transaction Record Completeness (Task 10.5)

**Admin Features (Properties 24-26):**
- [ ] Property 24: Admin Wallet Aggregation (Task 13.2)
- [ ] Property 25: Platform Revenue Calculation (Task 13.3)
- [ ] Property 26: Survival Rate Calculation (Task 13.4)

**Withdrawals (Properties 28-32):**
- [ ] Property 28: Withdrawal Balance Validation (Task 16.3)
- [ ] Property 29: Minimum Withdrawal Validation (Task 16.4)
- [ ] Property 30: Withdrawal Fee Deduction (Task 16.5)
- [ ] Property 31: Withdrawal Request Persistence (Task 16.6)
- [ ] Property 32: Withdrawal Status Transition (Task 16.7)

**Conway API (Properties 33-37):**
- [ ] Property 33: Conway API Credit Transfer (Task 3.3)
- [ ] Property 34: Conway API Balance Check (Task 3.4)
- [ ] Property 35: Conway API Authentication (Task 3.5)
- [ ] Property 36: API Retry Logic (Task 3.6)
- [ ] Property 37: API Failure Notification (Task 3.7)

**Blockchain (Property 38):**
- [ ] Property 38: ERC20 Balance Query (Task 4.7)

**Revenue & Fees (Properties 46-55):**
- [ ] Property 46: Performance Fee Calculation (Task 8.3)
- [ ] Property 47: Performance Fee Transaction Logging (Task 8.4)
- [ ] Property 48: Performance Fee Balance Transfer (Task 8.5)
- [ ] Property 49: Profit Transaction Recording (Task 8.6)
- [ ] Property 50: Loss Transaction Recording (Task 8.7)
- [ ] Property 51: Net Profit Calculation (Task 8.8)
- [ ] Property 52: Revenue Report Aggregation (Task 8.9)
- [ ] Property 53: Time-Based Revenue Breakdown (Task 8.10)
- [ ] Property 54: Revenue Source Breakdown (Task 8.11)
- [ ] Property 55: Top Revenue Agents (Task 8.12)


## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP, but are strongly recommended for production
- 5 out of 55 property tests are complete (Properties 1, 2, 3, 5, 7, 8)
- Each property test should run minimum 100 iterations using the `hypothesis` library for Python
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and allow for user feedback
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows
- Background services run continuously to monitor deposits, balances, and collect fees
- Security is built in from the start with encryption, audit logging, and rate limiting
- Error handling ensures graceful degradation and user-friendly messages
- Admin dashboard provides visibility into platform health and revenue

## Implementation Progress

**Phase 1: Database & Core Infrastructure (Complete ✅)**
- ✅ Database schema created with all tables and indexes
- ✅ Wallet manager with encryption
- ✅ Conway API integration with retry logic
- ✅ Deposit monitor service
- ✅ 5 property tests implemented

**Phase 2: Business Logic (Complete ✅)**
- ✅ Automaton manager with spawn and status tracking
- ✅ Balance monitor with alerts
- ✅ Revenue manager with fee collection
- ✅ Error handling framework

**Phase 3: UI Integration (Complete ✅)**
- ✅ Telegram bot handlers for all commands
- ✅ Menu system integration with AI Agent submenu
- ✅ Notification system for all events
- ✅ Admin dashboard with wallet, revenue, and agent statistics

**Phase 4: Background Services (Complete ✅)**
- ✅ Background service orchestration
- ✅ Bot integration with graceful shutdown
- ✅ Health check endpoint

**Phase 5: Hardening & Testing (In Progress 🔄)**
- 🔄 Property-based tests (5/55 complete, 9% coverage)
- ⏳ Withdrawal processing (not started)
- ⏳ Security hardening (audit logging, rate limiting, key rotation)
- ⏳ Documentation (deployment guide, user guide)

## Estimated Timeline

- Phase 1 (Tasks 1-5): Database and Core Infrastructure - ✅ Complete
- Phase 2 (Tasks 6-9): Business Logic and Services - ✅ Complete
- Phase 3 (Tasks 10-13): UI Integration - ✅ Complete
- Phase 4 (Tasks 14-15): Background Services - ✅ Complete
- Phase 5 (Tasks 16-20): Hardening, Testing & Deployment - 🔄 In Progress (20% complete)

**Current Status:** Core feature complete and deployed to production. Background services operational. Property-based testing and withdrawal processing remain as enhancement tasks.

## Testing Configuration

**Property-Based Testing Framework:** `hypothesis` for Python

**Test Configuration:**
```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)  # Minimum 100 iterations
@given(
    user_id=st.integers(min_value=1000000, max_value=9999999),
    deposit_amount=st.floats(min_value=5.0, max_value=10000.0)
)
def test_property_name(user_id, deposit_amount):
    # Feature: automaton-integration, Property N: Property Description
    # Test implementation
    pass
```

**Test Tag Format:**
```python
# Feature: automaton-integration, Property {number}: {property_text}
```

**Coverage Goals:**
- Line Coverage: Minimum 85%
- Branch Coverage: Minimum 80%
- Property Coverage: 100% of correctness properties tested (55/55)
- Integration Coverage: All critical workflows tested

## Deployment Checklist

**Environment Variables Required:**
- `TELEGRAM_BOT_TOKEN` - Telegram bot API token
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `POLYGON_RPC_URL` - Polygon network RPC endpoint
- `WALLET_ENCRYPTION_KEY` - Fernet encryption key (base64)
- `CONWAY_API_URL` - Conway Cloud API base URL
- `CONWAY_API_KEY` - Conway Cloud API authentication key
- `ADMIN_IDS` - Comma-separated list of admin Telegram IDs

**Database Migrations:**
1. Create custodial_wallets table with indexes
2. Create wallet_deposits table with indexes
3. Create wallet_withdrawals table with indexes
4. Create user_automatons table with indexes
5. Create automaton_transactions table with indexes
6. Create platform_revenue table with indexes

**Background Services:**
- Deposit Monitor (30 second interval)
- Balance Monitor (1 hour interval)
- Performance Fee Collector (5 minute interval)
- Health Check (1 minute interval)

**Monitoring:**
- Deposit detection latency
- Conway API response time
- Spawn success rate
- Agent survival rate
- Platform revenue (real-time)
- Error rates by category

## Security Checklist

- [x] Master encryption key stored in Railway secrets (not in code)
- [x] Private keys never logged or exposed in responses
- [ ] API keys rotated every 90 days (scheduled task needed)
- [x] Database uses parameterized queries (no SQL injection)
- [x] Input validation on all user inputs
- [ ] Rate limiting on spawn operations (1 per hour per user)
- [x] Admin commands restricted by telegram ID
- [ ] Audit logging for all sensitive operations
- [ ] Regular security audits scheduled

## Rollback Plan

If critical issues are discovered in production:
1. Disable spawn functionality via feature flag (set SPAWN_ENABLED=false)
2. Stop deposit monitor to prevent new deposits (stop background service)
3. Notify all users of maintenance via broadcast
4. Fix issues in staging environment
5. Test thoroughly with property tests (run all 55 tests with 1000 iterations)
6. Re-enable features gradually (spawn first, then deposits)
7. Monitor closely for 24 hours (watch logs, metrics, user feedback)

