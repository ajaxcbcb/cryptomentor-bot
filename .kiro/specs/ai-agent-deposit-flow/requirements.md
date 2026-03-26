# Requirements Document: AI Agent Deposit-First Flow

## Introduction

This feature implements a mandatory deposit-first flow for the AI Agent (Automaton) menu in the Telegram bot. Users must deposit USDT/USDC to a custodial wallet before accessing AI Agent features. The deposit creates Conway credits (fuel for autonomous trading agents) at a conversion rate of 1 USDT/USDC = 100 Conway Credits.

## Glossary

- **AI_Agent_Menu**: The Telegram bot menu interface for spawning and managing autonomous trading agents
- **Custodial_Wallet**: A bot-managed wallet that holds user deposits (USDC) and Conway credits
- **Conway_Credits**: Virtual currency used as fuel for AI trading agents (1 USDT/USDC = 100 credits)
- **Deposit_Flow**: The process of showing deposit instructions and wallet address to users
- **First_Deposit_Check**: Validation that verifies if a user has made their initial deposit
- **Deposit_Guide**: Step-by-step instructions for depositing USDT/USDC
- **QR_Code**: Visual representation of the deposit wallet address for easy scanning
- **Supported_Networks**: Blockchain networks accepted for deposits (Polygon, Base, Arbitrum)
- **Minimum_Deposit**: The smallest acceptable deposit amount (5 USDT/USDC)

## Requirements

### Requirement 1: First Deposit Detection

**User Story:** As a new user, I want the system to detect if I have made a deposit, so that I can access AI Agent features only after depositing.

#### Acceptance Criteria

1. WHEN a user clicks the AI Agent menu button, THE System SHALL check if the user has a custodial wallet with balance
2. WHEN checking wallet balance, THE System SHALL consider both USDC balance and Conway credits balance
3. IF the user has zero balance in both USDC and Conway credits, THEN THE System SHALL display the deposit requirement message
4. IF the user has any positive balance in USDC or Conway credits, THEN THE System SHALL display the full AI Agent menu
5. THE System SHALL query the custodial_wallets table in Supabase to retrieve balance information

### Requirement 2: Deposit Requirement Message

**User Story:** As a new user without a deposit, I want to see a clear message explaining the deposit requirement, so that I understand what I need to do to access AI Agent features.

#### Acceptance Criteria

1. WHEN displaying the deposit requirement message, THE System SHALL show a welcome message explaining that deposits are required
2. THE System SHALL display two action buttons: "💰 Deposit Sekarang" and "❓ Cara Deposit"
3. THE System SHALL use the callback identifier "automaton_first_deposit" for the deposit button
4. THE System SHALL use the callback identifier "deposit_guide" for the guide button
5. THE Message SHALL clearly communicate that Conway credits are needed to spawn AI agents

### Requirement 3: First Deposit Handler

**User Story:** As a new user, I want to initiate a deposit when I click the deposit button, so that I can receive my wallet address and deposit instructions.

#### Acceptance Criteria

1. WHEN a user clicks the "💰 Deposit Sekarang" button, THE System SHALL trigger the automaton_first_deposit callback handler
2. WHEN the handler is triggered, THE System SHALL generate or retrieve the user's custodial wallet
3. WHEN a new wallet is generated, THE System SHALL store it in the custodial_wallets table with encrypted private key
4. THE System SHALL display the wallet's deposit address as text
5. THE System SHALL generate and display a QR code image of the deposit address
6. THE System SHALL show deposit instructions including supported networks and minimum deposit amount
7. THE System SHALL inform the user that deposits will be automatically converted to Conway credits

### Requirement 4: Deposit Guide Handler

**User Story:** As a new user, I want to view detailed deposit instructions, so that I can understand how to deposit correctly and avoid mistakes.

#### Acceptance Criteria

1. WHEN a user clicks the "❓ Cara Deposit" button, THE System SHALL trigger the deposit_guide callback handler
2. THE System SHALL display step-by-step deposit instructions
3. THE System SHALL list all supported networks: Polygon (recommended), Base, and Arbitrum
4. THE System SHALL specify the minimum deposit amount of 5 USDT/USDC
5. THE System SHALL explain the conversion rate: 1 USDT/USDC = 100 Conway Credits
6. THE System SHALL provide troubleshooting tips for common deposit issues
7. THE System SHALL include a button to return to the deposit flow

### Requirement 5: Wallet Generation and Storage

**User Story:** As a system, I want to generate custodial wallets securely, so that user deposits are safe and properly tracked.

#### Acceptance Criteria

1. WHEN generating a new custodial wallet, THE System SHALL create a unique Ethereum-compatible wallet address
2. THE System SHALL encrypt the wallet's private key before storing it in the database
3. THE System SHALL initialize the wallet with zero balance_usdc and zero conway_credits
4. THE System SHALL associate the wallet with the user's Telegram ID
5. IF a user already has a custodial wallet, THEN THE System SHALL retrieve the existing wallet instead of creating a new one

### Requirement 6: Deposit Address Display

**User Story:** As a user initiating a deposit, I want to see my deposit address clearly with a QR code, so that I can easily copy or scan it for depositing.

#### Acceptance Criteria

1. WHEN displaying the deposit address, THE System SHALL show the full address as copyable text
2. THE System SHALL generate a QR code image containing the wallet address
3. THE System SHALL send the QR code as an image message in Telegram
4. THE System SHALL include network selection instructions in the message
5. THE System SHALL warn users to only use supported networks to avoid loss of funds

### Requirement 7: Callback Handler Integration

**User Story:** As a developer, I want callback handlers properly integrated into the menu system, so that button clicks trigger the correct functions.

#### Acceptance Criteria

1. THE System SHALL register the automaton_first_deposit callback in the handle_callback_query method
2. THE System SHALL register the deposit_guide callback in the handle_callback_query method
3. WHEN a callback is triggered, THE System SHALL route it to the appropriate handler function
4. THE System SHALL handle callback queries asynchronously to prevent blocking
5. IF a callback handler encounters an error, THEN THE System SHALL log the error and show a user-friendly error message

### Requirement 8: Network and Fee Information

**User Story:** As a user, I want to know which networks are supported and their fees, so that I can choose the most cost-effective option for depositing.

#### Acceptance Criteria

1. THE Deposit_Guide SHALL list Polygon as the recommended network with lowest fees
2. THE Deposit_Guide SHALL list Base as an alternative network option
3. THE Deposit_Guide SHALL list Arbitrum as an alternative network option
4. THE Deposit_Guide SHALL warn that using unsupported networks will result in loss of funds
5. THE Deposit_Guide SHALL recommend checking current network fees before depositing

### Requirement 9: Minimum Deposit Validation

**User Story:** As a system, I want to enforce minimum deposit requirements, so that deposits are economically viable for processing.

#### Acceptance Criteria

1. THE System SHALL specify a minimum deposit of 5 USDT/USDC in all deposit instructions
2. THE System SHALL display the minimum deposit amount in the deposit guide
3. THE System SHALL display the minimum deposit amount in the first deposit handler message
4. THE Deposit_Monitor SHALL validate deposits meet the minimum threshold (handled by existing system)
5. THE System SHALL explain that deposits below minimum may not be credited

### Requirement 10: Conversion Rate Display

**User Story:** As a user, I want to see the conversion rate from USDT/USDC to Conway credits, so that I know how many credits I will receive.

#### Acceptance Criteria

1. THE System SHALL display the conversion rate "1 USDT/USDC = 100 Conway Credits" in deposit instructions
2. THE System SHALL show example conversions (e.g., "5 USDT = 500 Conway Credits")
3. THE Deposit_Guide SHALL explain that Conway credits are used as fuel for AI agents
4. THE System SHALL clarify that the conversion happens automatically after deposit confirmation
5. THE System SHALL inform users that Conway credits cannot be converted back to USDT/USDC
