# Implementation Plan: Dual-Mode Offline-Online Bot System

## Overview

This implementation plan breaks down the dual-mode bot system into actionable coding tasks. The system enables users to switch between offline mode (manual trading with Binance API, no LLM) and online mode (AI agent trading with Automaton, LLM-powered). Each task builds incrementally on previous work, with property-based tests integrated throughout to validate correctness properties early.

## Tasks

- [x] 1. Set up core infrastructure and database schema
  - Create database migration file for all 5 tables (user_mode_states, online_sessions, isolated_ai_agents, automaton_credit_transactions, mode_transition_log)
  - Add indexes for performance optimization
  - Create database connection utilities
  - _Requirements: 1.7, 4.4, 10.2_

- [x] 1.1 Write property test for mode persistence
  - **Property 14: Mode Persistence**
  - **Validates: Requirements 1.7**

- [x] 2. Implement ModeStateManager component
  - [x] 2.1 Create ModeStateManager class with core methods
    - Implement get_user_mode(), set_user_mode(), is_offline_mode(), is_online_mode()
    - Implement transition_mode() with validation logic
    - Implement get_mode_history() for audit trail
    - _Requirements: 1.1, 1.2, 1.7, 1.8_

  - [x] 2.2 Write property test for mode activation with credit validation
    - **Property 1: Mode Activation with Credit Validation**
    - **Validates: Requirements 1.3, 1.4, 1.5, 1.6**

  - [x] 2.3 Write property test for state preservation during transitions
    - **Property 9: State Preservation During Transitions**
    - **Validates: Requirements 9.1, 9.2, 9.3**

  - [x] 2.4 Write property test for mode transition performance
    - **Property 15: Mode Transition Performance**
    - **Validates: Requirements 9.4, 9.5**

- [x] 3. Implement CreditManager component
  - [x] 3.1 Create CreditManager class with credit operations
    - Implement get_user_credits(), has_sufficient_credits()
    - Implement deduct_credits() and add_credits() with atomic transactions
    - Implement get_credit_history() for transaction logs
    - Implement validate_admin_balance() for Automaton API validation
    - _Requirements: 4.1, 4.2, 4.4, 4.6, 13.3, 13.5_

  - [x] 3.2 Write property test for credit tracking and logging
    - **Property 5: Credit Tracking and Logging**
    - **Validates: Requirements 4.2, 4.4, 4.6**

  - [x] 3.3 Write unit tests for credit edge cases
    - Test insufficient credits handling
    - Test negative credit amounts
    - Test concurrent credit operations
    - _Requirements: 4.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement OfflineModeHandler component
  - [x] 5.1 Create OfflineModeHandler class
    - Implement handle_analyze_command() using existing Binance integration
    - Implement handle_futures_command() for futures signals
    - Implement handle_manual_signal() for manual trading
    - Implement get_offline_menu() with inline keyboard
    - Implement format_offline_response() with [OFFLINE] prefix
    - Ensure no LLM calls in any offline operations
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7_

  - [x] 5.2 Write property test for offline mode feature access
    - **Property 2: Offline Mode Feature Access**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 5.3 Write unit tests for offline mode handlers
    - Test analyze command with various symbols
    - Test futures command with different timeframes
    - Test menu generation
    - _Requirements: 2.6_

- [x] 6. Implement SessionManager component
  - [x] 6.1 Create SessionManager class
    - Implement create_session() with unique session ID generation
    - Implement get_session() and is_session_active()
    - Implement close_session() with graceful cleanup
    - Implement update_session_activity() for tracking
    - _Requirements: 3.1, 9.2_

  - [x] 6.2 Write unit tests for session lifecycle
    - Test session creation and retrieval
    - Test session expiration
    - Test concurrent sessions
    - _Requirements: 3.1_

- [x] 7. Implement AIAgentManager component
  - [x] 7.1 Create AIAgentManager class
    - Implement get_or_create_agent() with lazy initialization
    - Implement initialize_agent() with Genesis Prompt injection
    - Implement is_agent_isolated() for security validation
    - Implement delete_agent() for cleanup
    - _Requirements: 3.2, 10.1, 10.2, 10.5, 11.2_

  - [x] 7.2 Write property test for online mode initialization
    - **Property 3: Online Mode Initialization**
    - **Validates: Requirements 3.1, 3.2**

  - [x] 7.3 Write property test for agent isolation
    - **Property 10: Agent Isolation**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

- [x] 8. Implement GenesisPromptLoader component
  - [x] 8.1 Create GenesisPromptLoader class
    - Implement load_prompt() from file (AUTOMATON_GENESIS_PROMPT.md)
    - Implement in-memory caching for performance
    - Implement reload_prompt() for updates
    - Implement get_current_prompt() and get_prompt_version()
    - _Requirements: 11.1, 11.2, 11.4, 11.5_

  - [x] 8.2 Write property test for Genesis Prompt injection
    - **Property 11: Genesis Prompt Injection**
    - **Validates: Requirements 11.2, 11.5, 11.6**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement AutomatonBridge component
  - [x] 10.1 Create AutomatonBridge class with API integration
    - Implement send_message() to Automaton API
    - Implement get_agent_status() for health checks
    - Implement validate_api_connection() for connectivity validation
    - Implement get_admin_balance() for credit validation
    - Implement deduct_admin_credits() for admin balance management
    - Configure API timeout, max retries, and backoff factor
    - _Requirements: 3.3, 13.1, 13.3, 13.4, 13.10_

  - [x] 10.2 Implement retry logic with exponential backoff
    - Implement retry_with_backoff() with configurable max retries
    - Add timeout handling and error recovery
    - Ensure no credit deduction on failed retries
    - _Requirements: 12.2, 12.3_

  - [x] 10.3 Write property test for retry logic with exponential backoff
    - **Property 12: Error Handling with Retry Logic**
    - **Validates: Requirements 12.2, 12.3**

  - [x] 10.4 Write property test for Automaton API credit validation
    - **Property 13: Automaton API Credit Validation**
    - **Validates: Requirements 13.1, 13.2, 13.3, 13.5, 13.10**

  - [x] 10.5 Write unit tests for API error scenarios
    - Test connection timeout
    - Test authentication failure
    - Test rate limiting
    - _Requirements: 12.1, 13.2, 13.7_

- [ ] 11. Implement OnlineModeHandler component
  - [x] 11.1 Create OnlineModeHandler class
    - Implement activate_online_mode() with credit check and session creation
    - Implement deactivate_online_mode() with graceful cleanup
    - Implement handle_user_message() with AI agent forwarding
    - Implement get_online_menu() with inline keyboard
    - Implement format_online_response() with [ONLINE - AI] prefix and credit display
    - _Requirements: 1.4, 1.5, 3.3, 3.6, 3.8, 3.9_

  - [-] 11.2 Write property test for online mode message handling with credit management
    - **Property 4: Online Mode Message Handling with Credit Management**
    - **Validates: Requirements 3.3, 3.8, 3.9**

  - [ ] 11.3 Write property test for AI agent transaction processing
    - **Property 7: AI Agent Transaction Processing**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6, 7.7**

  - [ ] 11.4 Write unit tests for online mode handlers
    - Test activation with sufficient credits
    - Test activation with insufficient credits
    - Test message forwarding to AI agent
    - _Requirements: 1.6, 4.5_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement command handlers
  - [ ] 13.1 Implement /offline command handler
    - Add command registration
    - Implement mode switch to offline
    - Display offline menu and welcome message
    - _Requirements: 1.1, 1.3, 8.6_

  - [ ] 13.2 Implement /online command handler
    - Add command registration
    - Implement credit check before activation
    - Implement mode switch to online with session creation
    - Display online menu and welcome message
    - _Requirements: 1.2, 1.4, 1.5, 1.6, 8.6_

  - [ ] 13.3 Implement /credits command handler
    - Add command registration
    - Display current Automaton credit balance
    - Display information on how to obtain credits
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 13.4 Implement /status command handler
    - Add command registration
    - Display current active mode
    - Display system health information
    - Display session information if in online mode
    - _Requirements: 8.7, 12.7_

  - [ ] 13.5 Update /admin command handler for credit management
    - Add "Add Credits" option to admin menu
    - Implement admin credit grant flow with user ID and amount prompts
    - Implement Automaton API balance validation before granting
    - Send confirmation to admin and notification to user
    - Add audit logging for all admin actions
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 13.1, 13.4, 13.8, 13.9_

  - [ ] 13.6 Write property test for admin credit grant flow
    - **Property 6: Admin Credit Grant Flow**
    - **Validates: Requirements 6.3, 6.4, 6.5, 6.6**

  - [ ] 13.7 Write unit tests for command handlers
    - Test all command registrations
    - Test command error handling
    - Test admin validation
    - _Requirements: 6.8_

- [ ] 14. Implement mode-aware message routing
  - [ ] 14.1 Create message router with mode detection
    - Implement router that checks user's current mode
    - Route offline mode messages to OfflineModeHandler
    - Route online mode messages to OnlineModeHandler
    - Handle mode transitions during active conversations
    - _Requirements: 1.8, 3.3_

  - [ ] 14.2 Write integration tests for message routing
    - Test routing in offline mode
    - Test routing in online mode
    - Test routing during mode transitions
    - _Requirements: 9.3_

- [ ] 15. Implement UI/UX enhancements
  - [ ] 15.1 Add mode-specific prefixes and emojis
    - Add [OFFLINE] 📊 prefix to all offline responses
    - Add [ONLINE - AI] 🤖 prefix to all online responses
    - Implement mode-specific emoji sets
    - _Requirements: 8.2, 8.3, 8.4_

  - [ ] 15.2 Create mode-specific menus
    - Design offline menu with technical analysis and futures options
    - Design online menu with AI agent options
    - Implement menu switching on mode change
    - _Requirements: 2.5, 8.5_

  - [ ] 15.3 Add loading indicators and welcome messages
    - Implement loading indicator for mode transitions
    - Create welcome messages for each mode
    - Add transition confirmation messages
    - _Requirements: 8.6, 9.4_

  - [ ] 15.4 Write property test for mode-specific UI presentation
    - **Property 8: Mode-Specific UI Presentation**
    - **Validates: Requirements 8.2, 8.3, 8.5, 8.6**

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Implement error handling and fallback mechanisms
  - [ ] 17.1 Add Automaton service fallback
    - Implement service availability check
    - Display error message suggesting offline mode on failure
    - Add admin notification for critical errors
    - _Requirements: 12.1, 12.5_

  - [ ] 17.2 Write property test for Automaton service fallback
    - **Property 19: Automaton Service Fallback**
    - **Validates: Requirements 12.1**

  - [ ] 17.3 Add transition error recovery
    - Implement error handling for failed transitions
    - Keep user in previous mode on error
    - Log failed transitions for monitoring
    - _Requirements: 9.6, 9.7_

  - [ ] 17.4 Write property test for transition error recovery
    - **Property 16: Transition Error Recovery**
    - **Validates: Requirements 9.6, 9.7**

  - [ ] 17.5 Add database fallback with local cache
    - Implement cache layer for read operations
    - Add fallback logic for database unavailability
    - _Requirements: 12.6_

  - [ ] 17.6 Implement comprehensive error logging
    - Add structured logging for all error categories
    - Implement log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Add error context and stack traces
    - _Requirements: 12.4_

  - [ ] 17.7 Write property test for critical error notification
    - **Property 20: Critical Error Notification**
    - **Validates: Requirements 12.4, 12.5**

  - [ ] 17.8 Write unit tests for error scenarios
    - Test all error handlers
    - Test fallback mechanisms
    - Test admin notifications
    - _Requirements: 12.1, 12.2, 12.3_

- [ ] 18. Implement audit logging and monitoring
  - [ ] 18.1 Add audit logging for admin actions
    - Log all credit grant operations
    - Log all admin menu accesses
    - Include user ID, action type, timestamp, and details
    - _Requirements: 4.4, 6.7, 13.8_

  - [ ] 18.2 Write property test for audit logging
    - **Property 18: Audit Logging**
    - **Validates: Requirements 6.7**

  - [ ] 18.3 Add mode transition logging
    - Log all mode transitions with success/failure status
    - Log transition duration for performance monitoring
    - Include error messages for failed transitions
    - _Requirements: 9.7_

  - [ ] 18.4 Add credit transaction logging
    - Log all credit additions and deductions
    - Include balance before and after
    - Log admin balance changes for Automaton API
    - _Requirements: 4.4, 13.9_

- [ ] 19. Implement first deposit auto-activation
  - [ ] 19.1 Add deposit detection and auto-activation
    - Detect user's first successful deposit
    - Automatically activate online mode
    - Direct user to AI agent with welcome message
    - _Requirements: 5.6_

  - [ ] 19.2 Write property test for first deposit auto-activation
    - **Property 17: First Deposit Auto-Activation**
    - **Validates: Requirements 5.6**

  - [ ] 19.3 Write integration test for deposit flow
    - Test complete deposit flow from admin grant to auto-activation
    - Test notification delivery
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 21. Integration and wiring
  - [ ] 21.1 Wire all components together
    - Connect ModeStateManager to command handlers
    - Connect CreditManager to OnlineModeHandler
    - Connect SessionManager and AIAgentManager to OnlineModeHandler
    - Connect AutomatonBridge to AIAgentManager
    - Connect GenesisPromptLoader to AIAgentManager
    - Integrate error handlers across all components
    - _Requirements: All requirements_

  - [ ] 21.2 Write end-to-end integration tests
    - Test complete offline mode flow
    - Test complete online mode flow
    - Test mode switching flow
    - Test admin credit grant flow
    - Test error recovery flows
    - _Requirements: All requirements_

  - [ ] 21.3 Add configuration management
    - Create configuration file for Automaton API settings
    - Add environment variable validation
    - Implement configuration reload without restart
    - _Requirements: 11.4_

- [ ] 22. Performance optimization
  - [ ] 22.1 Optimize database queries
    - Add connection pooling
    - Optimize indexes for frequent queries
    - Implement query result caching
    - _Requirements: 9.5_

  - [ ] 22.2 Optimize mode transitions
    - Minimize database queries during transitions
    - Implement async operations where possible
    - Add performance monitoring
    - _Requirements: 9.5_

  - [ ] 22.3 Optimize Genesis Prompt loading
    - Implement in-memory caching
    - Add lazy loading for agents
    - _Requirements: 11.1, 11.4_

- [ ] 23. Final checkpoint - Ensure all tests pass
  - Run complete test suite
  - Verify all property tests pass with 100+ iterations
  - Verify all integration tests pass
  - Check test coverage (target: >90% line coverage, >85% branch coverage)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties with randomized inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows across components
- All components use Python 3.10+ with type hints and dataclasses
- Database operations use Supabase (PostgreSQL)
- Automaton API integration uses retry logic with exponential backoff
- Error handling includes fallback mechanisms and admin notifications
- Audit logging tracks all admin actions and credit transactions
- UI/UX provides clear visual distinction between offline and online modes
