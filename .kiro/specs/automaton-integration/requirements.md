# Requirements Document: Automaton Integration

## Introduction

This document specifies the requirements for integrating Automaton (autonomous AI trading agents) with the CryptoMentor AI Telegram bot. The integration will enable 1200+ existing users to spawn and manage autonomous trading agents that consume Conway credits as fuel, creating a new revenue stream while maintaining zero capital risk for the platform administrator.

## Glossary

- **Automaton**: An autonomous AI agent capable of self-funding, self-replication, and self-modification
- **Conway_Credits**: The fuel currency consumed by automatons to survive and operate (1 USDT = 100 Conway Credits)
- **Custodial_Wallet**: A user-specific Ethereum wallet for depositing USDT/USDC, managed by the platform with encrypted private keys
- **Deposit_Monitor**: A blockchain monitoring service that detects incoming USDT/USDC deposits to custodial wallets
- **Survival_Tier**: The operational state of an automaton based on available Conway credits (normal/low_compute/critical/dead)
- **Platform**: The CryptoMentor AI Telegram bot system
- **User**: A Telegram user interacting with the CryptoMentor AI bot
- **Admin**: Platform administrator with elevated privileges
- **Spawn_Fee**: One-time fee of 100,000 credits to create a new automaton
- **Bensin**: Indonesian term for "fuel" - refers to Conway credits that keep agents alive

## Requirements

### Requirement 1: Custodial Wallet Management

**User Story:** As a user, I want my own custodial wallet for depositing funds, so that I can fuel my automaton without the admin needing to provide capital.

#### Acceptance Criteria

1. WHEN a user spawns their first automaton, THE Platform SHALL generate a unique Ethereum wallet address for that user
2. WHEN generating a wallet, THE Platform SHALL encrypt the private key using Fernet encryption with a master key stored in environment variables
3. WHEN a wallet is created, THE Platform SHALL store the wallet address, encrypted private key, and user association in the custodial_wallets table
4. THE Platform SHALL ensure each user has exactly one custodial wallet that persists across multiple automatons
5. WHEN a user requests their deposit address, THE Platform SHALL display the wallet address with QR code and supported networks (Polygon, Base, Arbitrum)

### Requirement 2: Blockchain Deposit Detection

**User Story:** As a user, I want my deposits to be automatically detected, so that my automaton is fueled without manual intervention.

#### Acceptance Criteria

1. WHEN the Deposit_Monitor service runs, THE Platform SHALL check all custodial wallet balances every 30 seconds
2. WHEN a USDT or USDC deposit is detected, THE Platform SHALL record the transaction in the wallet_deposits table with status 'pending'
3. WHEN a deposit reaches 12 confirmations, THE Platform SHALL update the deposit status to 'confirmed'
4. WHEN a deposit is confirmed, THE Platform SHALL convert the amount to Conway credits at the rate of 1 USDT = 100 Conway Credits
5. WHEN Conway credits are calculated, THE Platform SHALL credit the user's automaton account via the Conway Cloud API
6. WHEN credits are successfully added, THE Platform SHALL send a Telegram notification to the user with deposit amount and credited Conway credits

### Requirement 3: Conway Credits Conversion

**User Story:** As a user, I want my USDT/USDC deposits to be automatically converted to Conway credits, so that my automaton can consume them for survival.

#### Acceptance Criteria

1. THE Platform SHALL apply the conversion rate of 1 USDT = 100 Conway Credits for all deposits
2. THE Platform SHALL apply the conversion rate of 1 USDC = 100 Conway Credits for all deposits
3. WHEN converting deposits, THE Platform SHALL deduct a 2% platform fee before crediting Conway credits
4. WHEN a deposit is below 5 USDT/USDC, THE Platform SHALL reject the deposit and notify the user of the minimum requirement
5. THE Platform SHALL update the custodial_wallets table with the new conway_credits balance after each successful conversion

### Requirement 4: Automaton Spawning

**User Story:** As a premium user, I want to spawn an autonomous trading agent, so that it can trade on my behalf using Conway credits as fuel.

#### Acceptance Criteria

1. WHEN a user initiates agent spawning, THE Platform SHALL verify the user has premium status
2. WHEN spawning is initiated, THE Platform SHALL verify the user has at least 100,000 credits available
3. WHEN verification passes, THE Platform SHALL deduct 100,000 credits from the user's account
4. WHEN credits are deducted, THE Platform SHALL generate a unique agent wallet address
5. WHEN the agent wallet is created, THE Platform SHALL provision a Conway API key for the agent
6. WHEN provisioning is complete, THE Platform SHALL deploy the agent to Railway with the genesis prompt
7. WHEN deployment succeeds, THE Platform SHALL register the agent in the user_automatons table with status 'active'
8. WHEN registration is complete, THE Platform SHALL send the user a confirmation message with agent details (name, wallet, credits, status)

### Requirement 5: Agent Status Monitoring

**User Story:** As a user, I want to check my automaton's status, so that I know its survival tier and remaining fuel.

#### Acceptance Criteria

1. WHEN a user requests agent status, THE Platform SHALL retrieve the agent record from user_automatons table
2. WHEN displaying status, THE Platform SHALL show agent name, wallet address, Conway credits balance, and survival tier
3. WHEN calculating survival tier, THE Platform SHALL classify as 'critical' if credits < 1000, 'low_compute' if credits < 5000, otherwise 'normal'
4. WHEN displaying status, THE Platform SHALL show last activity timestamp and estimated runtime in days
5. WHEN displaying status, THE Platform SHALL show total earnings and total expenses from automaton_transactions table

### Requirement 6: Low Balance Alerts

**User Story:** As a user, I want to be notified when my automaton is running low on fuel, so that I can deposit more funds before it stops.

#### Acceptance Criteria

1. WHEN the balance monitor runs hourly, THE Platform SHALL check all active automatons' Conway credit balances
2. WHEN an automaton has less than 1000 credits and greater than 0 credits, THE Platform SHALL send a critical alert to the user
3. WHEN an automaton has less than 5000 credits and greater than or equal to 1000 credits, THE Platform SHALL send a warning alert to the user
4. WHEN sending a critical alert, THE Platform SHALL include current balance, estimated runtime (< 1 day), and deposit instructions
5. WHEN sending a warning alert, THE Platform SHALL include current balance, estimated runtime in days, and deposit recommendation

### Requirement 7: Menu Integration

**User Story:** As a user, I want to access automaton features through the main menu, so that I can easily manage my agents.

#### Acceptance Criteria

1. WHEN the main menu is displayed, THE Platform SHALL include a "🤖 AI Agent" button
2. WHEN the AI Agent button is clicked, THE Platform SHALL display a submenu with options: Spawn Agent, Agent Status, Fund Agent, Agent Logs, Agent Settings
3. WHEN "Spawn Agent" is selected, THE Platform SHALL initiate the spawning workflow
4. WHEN "Agent Status" is selected, THE Platform SHALL display the current agent status
5. WHEN "Fund Agent" is selected, THE Platform SHALL display the deposit address with QR code

### Requirement 8: Deposit Address Display

**User Story:** As a user, I want to see my deposit address with clear instructions, so that I can easily fund my automaton.

#### Acceptance Criteria

1. WHEN a user requests the deposit address, THE Platform SHALL display the custodial wallet address in monospace format for easy copying
2. WHEN displaying the address, THE Platform SHALL generate and show a QR code image for mobile wallet scanning
3. WHEN displaying deposit instructions, THE Platform SHALL list supported networks (Polygon recommended, Base, Arbitrum)
4. WHEN displaying conversion rates, THE Platform SHALL show 1 USDT = 100 Conway Credits and 1 USDC = 100 Conway Credits
5. WHEN displaying requirements, THE Platform SHALL show minimum deposit of 5 USDT and warn against sending other tokens

### Requirement 9: Agent Transaction Logging

**User Story:** As a user, I want to see my automaton's transaction history, so that I can track how credits are being consumed and earned.

#### Acceptance Criteria

1. WHEN a user requests agent logs, THE Platform SHALL retrieve the last 20 transactions from automaton_transactions table
2. WHEN displaying transactions, THE Platform SHALL show transaction type (spawn, fund, earn, spend), amount, description, and timestamp
3. WHEN displaying earnings, THE Platform SHALL highlight positive amounts in green
4. WHEN displaying expenses, THE Platform SHALL highlight negative amounts in red
5. WHEN no transactions exist, THE Platform SHALL display a message indicating the agent has no transaction history yet

### Requirement 10: Admin Wallet Monitoring

**User Story:** As an admin, I want to monitor all custodial wallets, so that I can track platform health and revenue.

#### Acceptance Criteria

1. WHEN an admin requests wallet summary, THE Platform SHALL calculate total USDT and USDC balances across all custodial wallets
2. WHEN displaying summary, THE Platform SHALL show total number of wallets, total balances, all-time deposits, and all-time spending
3. WHEN calculating platform revenue, THE Platform SHALL compute 10% of (total_deposited - total_spent)
4. WHEN displaying summary, THE Platform SHALL show count of active agents and overall survival rate percentage
5. WHEN an admin requests specific wallet details, THE Platform SHALL display full transaction history for that user's wallet

### Requirement 11: Security and Encryption

**User Story:** As a platform administrator, I want all private keys encrypted, so that user funds are protected from unauthorized access.

#### Acceptance Criteria

1. THE Platform SHALL use Fernet symmetric encryption for all private key storage
2. THE Platform SHALL store the master encryption key in Railway environment variables, never in code or database
3. WHEN decrypting a private key, THE Platform SHALL only allow the wallet_manager module to perform decryption
4. THE Platform SHALL log all private key decryption events to the audit log
5. THE Platform SHALL rotate the master encryption key every 90 days with automated re-encryption of all stored keys

### Requirement 12: Withdrawal Support

**User Story:** As a user, I want to withdraw unused funds from my custodial wallet, so that I can recover my capital if needed.

#### Acceptance Criteria

1. WHEN a user initiates a withdrawal, THE Platform SHALL verify the user has sufficient USDT balance in their custodial wallet
2. WHEN a withdrawal amount is less than 10 USDT, THE Platform SHALL reject the request and notify the user of the minimum
3. WHEN a withdrawal is requested, THE Platform SHALL deduct a 1 USDT flat fee from the withdrawal amount
4. WHEN a withdrawal request is created, THE Platform SHALL store it in wallet_withdrawals table with status 'pending'
5. WHEN a withdrawal is processed, THE Platform SHALL update the status to 'completed' and record the transaction hash

### Requirement 13: Conway Cloud API Integration

**User Story:** As the platform, I want to integrate with Conway Cloud API, so that automatons can be funded and monitored programmatically.

#### Acceptance Criteria

1. WHEN funding an agent, THE Platform SHALL call the Conway Cloud API /credits/transfer endpoint with agent wallet and amount
2. WHEN checking agent balance, THE Platform SHALL call the Conway Cloud API /credits/balance endpoint with agent wallet
3. WHEN making API calls, THE Platform SHALL include the Conway API key in the Authorization header
4. WHEN an API call fails, THE Platform SHALL retry up to 3 times with exponential backoff
5. WHEN all retries fail, THE Platform SHALL log the error and notify the admin via Telegram

### Requirement 14: Database Schema Implementation

**User Story:** As a developer, I want proper database tables for custodial wallets and transactions, so that all data is persisted reliably.

#### Acceptance Criteria

1. THE Platform SHALL create a custodial_wallets table with columns: id, user_id, wallet_address, private_key_encrypted, balance_usdt, balance_usdc, conway_credits, created_at, last_deposit_at, total_deposited, total_spent
2. THE Platform SHALL create a wallet_deposits table with columns: id, wallet_id, user_id, tx_hash, from_address, amount, token, network, status, confirmations, detected_at, confirmed_at, credited_conway
3. THE Platform SHALL create a wallet_withdrawals table with columns: id, wallet_id, user_id, amount, token, to_address, tx_hash, status, requested_at, processed_at, fee
4. THE Platform SHALL create a user_automatons table with columns: id, user_id, agent_wallet, agent_name, genesis_prompt, conway_credits, survival_tier, created_at, last_active, status
5. THE Platform SHALL create an automaton_transactions table with columns: id, automaton_id, type, amount, description, timestamp

### Requirement 15: Polygon Network Integration

**User Story:** As a user, I want to deposit on Polygon network, so that I pay minimal gas fees for my transactions.

#### Acceptance Criteria

1. THE Platform SHALL connect to Polygon network via RPC URL stored in environment variables
2. WHEN monitoring deposits, THE Platform SHALL use the Polygon USDT contract address 0xc2132D05D31c914a87C6611C10748AEb04B58e8F
3. WHEN monitoring deposits, THE Platform SHALL use the Polygon USDC contract address 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
4. WHEN checking token balances, THE Platform SHALL call the ERC20 balanceOf function with the custodial wallet address
5. WHEN processing deposits, THE Platform SHALL wait for 12 block confirmations before crediting Conway credits

### Requirement 16: Agent Survival Tiers

**User Story:** As a user, I want my automaton to operate in different tiers based on available fuel, so that it can survive longer when credits are low.

#### Acceptance Criteria

1. WHEN Conway credits are >= 5000, THE Platform SHALL set survival_tier to 'normal' with full compute resources
2. WHEN Conway credits are >= 1000 and < 5000, THE Platform SHALL set survival_tier to 'low_compute' with reduced resources
3. WHEN Conway credits are > 0 and < 1000, THE Platform SHALL set survival_tier to 'critical' with minimal resources
4. WHEN Conway credits reach 0, THE Platform SHALL set survival_tier to 'dead' and status to 'paused'
5. WHEN an agent is in 'dead' tier, THE Platform SHALL prevent all agent operations until credits are added

### Requirement 17: Premium User Verification

**User Story:** As the platform, I want to restrict automaton spawning to premium users, so that this feature remains a premium benefit.

#### Acceptance Criteria

1. WHEN a user attempts to spawn an agent, THE Platform SHALL query the users table for is_premium status
2. WHEN is_premium is 0 or FALSE, THE Platform SHALL reject the spawn request with a message to upgrade to premium
3. WHEN is_premium is 1 or TRUE, THE Platform SHALL proceed with credit verification
4. WHEN a premium subscription expires, THE Platform SHALL NOT automatically stop existing agents
5. WHEN a premium subscription expires, THE Platform SHALL prevent spawning new agents until subscription is renewed

### Requirement 18: Credit System Integration

**User Story:** As a user, I want the spawn fee deducted from my existing credit balance, so that I can use my accumulated credits to spawn agents.

#### Acceptance Criteria

1. WHEN verifying spawn eligibility, THE Platform SHALL query the users table for the credits column
2. WHEN credits are less than 100,000, THE Platform SHALL reject the spawn request with current balance and required amount
3. WHEN credits are >= 100,000, THE Platform SHALL deduct exactly 100,000 credits from the user's balance
4. WHEN credits are deducted, THE Platform SHALL log the transaction in user_activity table with action 'agent_spawned'
5. WHEN the spawn process fails after credit deduction, THE Platform SHALL refund the 100,000 credits to the user

### Requirement 19: Error Handling and Recovery

**User Story:** As a user, I want clear error messages when something goes wrong, so that I know how to resolve issues.

#### Acceptance Criteria

1. WHEN wallet generation fails, THE Platform SHALL log the error and notify the user to contact support
2. WHEN deposit detection fails, THE Platform SHALL retry on the next monitoring cycle without notifying the user
3. WHEN Conway API calls fail, THE Platform SHALL log the error and notify the admin via Telegram
4. WHEN agent deployment fails, THE Platform SHALL refund the spawn fee and notify the user with error details
5. WHEN database operations fail, THE Platform SHALL rollback transactions and return a generic error message to the user

### Requirement 20: Notification System

**User Story:** As a user, I want to receive Telegram notifications for important events, so that I stay informed about my automaton's status.

#### Acceptance Criteria

1. WHEN a deposit is confirmed, THE Platform SHALL send a notification with amount, token, and credited Conway credits
2. WHEN an agent is successfully spawned, THE Platform SHALL send a notification with agent name, wallet, and initial credits
3. WHEN Conway credits fall below 5000, THE Platform SHALL send a warning notification with estimated runtime
4. WHEN Conway credits fall below 1000, THE Platform SHALL send a critical notification with urgent deposit instructions
5. WHEN an agent stops due to zero credits, THE Platform SHALL send a notification that the agent is now in 'dead' status

### Requirement 21: Platform Revenue Model

**User Story:** As a platform administrator, I want to collect fees from deposits and agent profits, so that the platform generates sustainable revenue.

#### Acceptance Criteria

1. WHEN processing a deposit, THE Platform SHALL deduct a 2% deposit fee before converting to Conway credits
2. WHEN an agent generates trading profits, THE Platform SHALL collect a 20% performance fee from the profit amount
3. WHEN calculating performance fees, THE Platform SHALL only apply the fee to realized profits (closed positions with positive P&L)
4. WHEN performance fees are collected, THE Platform SHALL record the transaction in automaton_transactions table with type 'platform_fee'
5. WHEN performance fees are collected, THE Platform SHALL update a platform_revenue table with fee amount, source agent, and timestamp

### Requirement 22: Agent Profit Tracking

**User Story:** As a user, I want to see my automaton's trading performance, so that I know if it's profitable.

#### Acceptance Criteria

1. WHEN an agent closes a profitable trade, THE Platform SHALL record the profit amount in automaton_transactions with type 'earn'
2. WHEN an agent closes a losing trade, THE Platform SHALL record the loss amount in automaton_transactions with type 'spend'
3. WHEN calculating total earnings, THE Platform SHALL sum all 'earn' transactions for the agent
4. WHEN calculating total expenses, THE Platform SHALL sum all 'spend' transactions plus Conway credit consumption
5. WHEN displaying agent status, THE Platform SHALL show net profit/loss as (total_earnings - total_expenses)

### Requirement 23: Performance Fee Distribution

**User Story:** As a platform administrator, I want performance fees automatically distributed, so that revenue is collected without manual intervention.

#### Acceptance Criteria

1. WHEN an agent realizes a profit, THE Platform SHALL calculate 20% of the profit as the performance fee
2. WHEN the performance fee is calculated, THE Platform SHALL transfer the fee amount from the agent's Conway credits to the platform wallet
3. WHEN the fee transfer succeeds, THE Platform SHALL update the agent's conway_credits balance in user_automatons table
4. WHEN the fee transfer succeeds, THE Platform SHALL record the transaction in automaton_transactions with type 'performance_fee'
5. WHEN the fee transfer fails, THE Platform SHALL retry up to 3 times and log the error if all retries fail

### Requirement 24: Revenue Reporting

**User Story:** As a platform administrator, I want to see revenue reports, so that I can track platform profitability.

#### Acceptance Criteria

1. WHEN an admin requests revenue report, THE Platform SHALL calculate total deposit fees collected
2. WHEN calculating revenue, THE Platform SHALL sum all performance fees collected from all agents
3. WHEN displaying the report, THE Platform SHALL show daily, weekly, and monthly revenue breakdowns
4. WHEN displaying the report, THE Platform SHALL show revenue by source (deposit fees vs performance fees)
5. WHEN displaying the report, THE Platform SHALL show top 10 revenue-generating agents
