# Implementation Plan: AI Agent Deposit-First Flow

## Overview

This implementation adds two callback handlers to enable the deposit-first flow for AI Agent access. The handlers leverage existing wallet generation and deposit monitoring infrastructure. All code will be added to `Bismillah/menu_handlers.py`.

## Tasks

- [x] 1. Add callback routing for deposit flow handlers
  - Add `automaton_first_deposit` callback routing in `handle_callback_query()` method
  - Add `deposit_guide` callback routing in `handle_callback_query()` method
  - Place routing after existing AI Agent menu callbacks
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 2. Implement first deposit handler
  - [x] 2.1 Create `handle_automaton_first_deposit()` method in MenuCallbackHandler class
    - Get user ID and language preference from query
    - Query Supabase for existing custodial wallet
    - If no wallet exists, generate new wallet (address + encrypted private key)
    - Store new wallet in custodial_wallets table with zero balances
    - Generate QR code URL for wallet address
    - Format deposit instructions message with wallet address, QR code, supported networks, conversion rates, and minimum deposit
    - Support both Indonesian and English languages
    - Send message with wallet address as copyable monospace text
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 2.2 Write unit tests for first deposit handler
    - Test wallet generation for new user
    - Test wallet retrieval for existing user
    - Test message formatting in Indonesian
    - Test message formatting in English
    - Test QR code URL generation
    - Test error handling for database failures
    - _Requirements: 3.1, 3.2, 3.3, 5.5, 6.1, 6.2_

  - [ ]* 2.3 Write property test for wallet address uniqueness
    - **Property 2: Wallet Address Uniqueness**
    - **Validates: Requirements 5.5**
    - Generate 100 random users
    - Create wallet for each user
    - Verify all addresses are unique
    - Call wallet creation again for each user
    - Verify same address returned (idempotence)

- [x] 3. Implement deposit guide handler
  - [x] 3.1 Create `handle_deposit_guide()` method in MenuCallbackHandler class
    - Get user language preference
    - Format comprehensive deposit guide with step-by-step instructions
    - List all supported networks: Polygon (recommended), Base, Arbitrum
    - Explain conversion rate: 1 USDT/USDC = 100 Conway Credits with examples
    - Specify minimum deposit: 5 USDT/USDC
    - Include troubleshooting tips for common issues
    - Add back button to return to deposit flow
    - Support both Indonesian and English languages
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 3.2 Write unit tests for deposit guide handler
    - Test guide message formatting in Indonesian
    - Test guide message formatting in English
    - Test all required information is present (networks, rates, minimum)
    - Test back button functionality
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 8.1, 8.2, 8.3, 9.1, 10.1_

  - [ ]* 3.3 Write property test for required information display
    - **Property 6-8: Information Display**
    - **Validates: Requirements 8.1, 8.2, 8.3, 9.1, 10.1**
    - Generate 100 deposit guide messages with random language preferences
    - Verify each message contains minimum deposit amount "5 USDT/USDC"
    - Verify each message contains conversion rate "1 USDT/USDC = 100 Conway Credits"
    - Verify each message contains all three networks: Polygon, Base, Arbitrum
    - Verify Polygon is marked as recommended

- [x] 4. Add error handling for all handlers
  - [x] 4.1 Add try-except blocks to both handlers
    - Catch Supabase connection errors
    - Catch wallet generation errors
    - Catch QR code generation errors (graceful degradation)
    - Log all errors with user ID and error details
    - Send user-friendly error messages
    - _Requirements: 7.5_

  - [ ]* 4.2 Write unit tests for error scenarios
    - Test Supabase connection failure handling
    - Test wallet generation failure handling
    - Test QR code API failure (should still show address)
    - Test user not found scenario
    - Verify error messages are user-friendly
    - Verify errors are logged correctly

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 6. Write integration tests for complete flow
  - [ ]* 6.1 Test end-to-end first deposit flow
    - Simulate user clicking AI Agent button without deposit
    - Verify deposit welcome message displays
    - Simulate clicking "💰 Deposit Sekarang" button
    - Verify wallet generation and address display
    - Verify QR code URL is correct
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 6.2 Test deposit guide flow
    - Simulate user clicking "❓ Cara Deposit" button
    - Verify guide displays with all required information
    - Verify back button returns to deposit welcome
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ]* 6.3 Test post-deposit access
    - Simulate user with existing deposit (balance > 0)
    - Verify full AI Agent menu displays
    - Verify no deposit message shown
    - _Requirements: 1.3, 1.4_

  - [ ]* 6.4 Write property test for deposit detection consistency
    - **Property 1: Deposit Detection Consistency**
    - **Validates: Requirements 1.3, 1.4**
    - Generate 100 random wallet states with various balance combinations
    - For each state, check if deposit detection returns correct result
    - Verify: balance_usdc > 0 OR conway_credits > 0 → has_deposit = True
    - Verify: balance_usdc == 0 AND conway_credits == 0 → has_deposit = False

  - [ ]* 6.5 Write property test for callback routing
    - **Property 4: Callback Routing Correctness**
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - Generate 100 callback queries with valid callback data
    - Test both `automaton_first_deposit` and `deposit_guide` callbacks
    - Verify each routes to correct handler without exceptions
    - Verify error handling for invalid callback data

  - [ ]* 6.6 Write property test for language consistency
    - **Property 5: Language Consistency**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
    - Generate 100 users with random language preferences (id/en)
    - For each user, generate all deposit flow messages
    - Verify all messages use the same language consistently
    - Verify no language mixing occurs within a single flow

- [ ] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- The deposit check logic in `show_ai_agent_menu()` is already implemented and requires no changes
- Wallet generation pattern can be reused from `spawn_agent_command()` in `handlers_automaton.py`
- QR code generation pattern can be reused from `deposit_command()` in `handlers_automaton.py`
- All new code will be added to `Bismillah/menu_handlers.py`
- No database schema changes required (uses existing `custodial_wallets` table)
- No new dependencies required
- Fully backward compatible with existing code
