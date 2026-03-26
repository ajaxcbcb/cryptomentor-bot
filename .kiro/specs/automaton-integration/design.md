# Design Document: Automaton Integration

## Overview

This design document describes the technical architecture for integrating Automaton (autonomous AI trading agents) with the CryptoMentor AI Telegram bot. The integration enables users to spawn and manage autonomous trading agents that consume Conway credits as fuel, creating a sustainable revenue model with zero capital risk for the platform.

### Key Design Principles

1. **Zero Capital Risk**: Users deposit to their own custodial wallets, not admin wallets
2. **Security First**: All private keys encrypted with Fernet, master key in environment variables
3. **Automated Operations**: Deposit detection, credit conversion, and fee collection are fully automated
4. **Scalability**: Architecture supports unlimited users and agents
5. **Fault Tolerance**: Retry mechanisms, transaction rollbacks, and error recovery
6. **User Experience**: Clear notifications, simple menu navigation, QR codes for deposits

### Technology Stack

- **Backend**: Python 3.x with python-telegram-bot library
- **Database**: Supabase (PostgreSQL) for primary storage, SQLite for local fallback
- **Blockchain**: Web3.py for Ethereum/Polygon interaction
- **Encryption**: Cryptography library (Fernet) for private key encryption
- **Deployment**: Railway for bot and agent hosting
- **External APIs**: Conway Cloud API for agent runtime management
- **Networks**: Polygon (primary), Base, Arbitrum for USDT/USDC deposits

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Menu Handler │  │ Command      │  │ Callback     │      │
│  │              │  │ Handlers     │  │ Handlers     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Wallet       │  │ Automaton    │  │ Revenue      │      │
│  │ Manager      │  │ Manager      │  │ Manager      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                           │
│  │ Lineage      │  (NEW: Parent-Child Revenue Sharing)     │
│  │ Manager      │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Background Services                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Deposit      │  │ Balance      │  │ Performance  │      │
│  │ Monitor      │  │ Monitor      │  │ Fee Collector│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                           │
│  │ Lineage      │  (NEW: Parent Revenue Distribution)      │
│  │ Fee Collector│                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┐
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Polygon RPC  │  │ Conway Cloud │  │ Supabase DB  │      │
│  │              │  │ API          │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Deposit Flow
```
User deposits USDT → Polygon Network → Custodial Wallet
                                            ↓
                                    Deposit Monitor detects
                                            ↓
                                    Wait 12 confirmations
                                            ↓
                                    Deduct 2% platform fee
                                            ↓
                                    Convert to Conway Credits (1:100)
                                            ↓
                                    Credit via Conway API
                                            ↓
                                    Notify user via Telegram
```

#### Agent Spawn Flow
```
User clicks "Spawn Agent" → Verify premium status
                                    ↓
                            Verify 100k credits
                                    ↓
                            Deduct 100k credits
                                    ↓
                            Generate agent wallet
                                    ↓
                            Provision Conway API key
                                    ↓
                            Deploy to Railway
                                    ↓
                            Register in database
                                    ↓
                            Notify user with details
```

#### Performance Fee Flow
```
Agent closes profitable trade → Calculate 20% fee
                                        ↓
                                Transfer fee from agent credits
                                        ↓
                                Record in transactions table
                                        ↓
                                Update platform revenue
                                        ↓
                                Update agent balance
```

#### Parent-Child Revenue Sharing Flow (NEW)
```
Child Agent earns profit → Calculate child's net earnings
                                        ↓
                            Check if child has parent agent
                                        ↓
                            Calculate parent share (10% of child's earnings)
                                        ↓
                            Transfer credits from child to parent
                                        ↓
                            Record lineage transaction
                                        ↓
                            Update both agent balances
                                        ↓
                            Notify parent owner of revenue share
```

## Components and Interfaces

### 1. Wallet Manager (`app/wallet_manager.py`)

**Purpose**: Manages custodial wallet generation, encryption, and retrieval.

**Key Methods**:

```python
class WalletManager:
    def __init__(self):
        """Initialize with Fernet cipher using master key from env"""
        
    def create_custodial_wallet(self, user_id: int) -> dict:
        """
        Generate new Ethereum wallet for user
        Returns: {
            'user_id': int,
            'wallet_address': str,
            'private_key_encrypted': str,
            'balance_usdt': float,
            'balance_usdc': float,
            'conway_credits': float
        }
        """
        
    def get_user_wallet(self, user_id: int) -> dict | None:
        """Retrieve user's custodial wallet from database"""
        
    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key for transaction signing (admin only)"""
        
    def get_wallet_balance(self, wallet_address: str, token: str) -> float:
        """Query blockchain for USDT/USDC balance"""
```

**Security Considerations**:
- Master encryption key stored in `WALLET_ENCRYPTION_KEY` environment variable
- Private keys never logged or exposed in API responses
- Decryption only allowed in wallet_manager module
- All decryption events logged to audit trail

### 2. Deposit Monitor (`app/deposit_monitor.py`)

**Purpose**: Continuously monitors custodial wallets for incoming USDT/USDC deposits.

**Key Methods**:

```python
class DepositMonitor:
    def __init__(self):
        """Initialize Web3 connection to Polygon network"""
        
    async def monitor_deposits(self):
        """
        Main monitoring loop - runs every 30 seconds
        Checks all custodial wallets for balance changes
        """
        
    def _check_token_balance(self, address: str, contract) -> float:
        """Query ERC20 token balance for address"""
        
    async def _process_deposit(self, wallet: dict, amount: float, token: str):
        """
        Process detected deposit:
        1. Update wallet balance in database
        2. Deduct 2% platform fee
        3. Convert to Conway credits (1:100)
        4. Credit via Conway API
        5. Notify user
        """
        
    async def _credit_conway(self, wallet: dict, credits: float):
        """Call Conway API to add credits to agent"""
        
    async def _notify_user_deposit(self, user_id: int, amount: float, 
                                   token: str, conway_credits: float):
        """Send Telegram notification about confirmed deposit"""
```

**Configuration**:
- Polygon RPC URL: `POLYGON_RPC_URL` environment variable
- USDT contract: `0xc2132D05D31c914a87C6611C10748AEb04B58e8F`
- USDC contract: `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`
- Monitoring interval: 30 seconds
- Confirmation threshold: 12 blocks

### 3. Automaton Manager (`app/automaton_manager.py`)

**Purpose**: Handles agent spawning, status tracking, and lifecycle management.

**Key Methods**:

```python
class AutomatonManager:
    def __init__(self):
        """Initialize with database and Conway API client"""
        
    async def spawn_agent(self, user_id: int, name: str, 
                         genesis_prompt: str) -> dict:
        """
        Spawn new autonomous agent:
        1. Verify premium status
        2. Verify 100k credits
        3. Deduct credits
        4. Generate agent wallet
        5. Provision Conway API key
        6. Deploy to Railway
        7. Register in database
        Returns agent details or error
        """
        
    def get_agent_status(self, user_id: int) -> dict:
        """
        Retrieve agent status including:
        - Agent name, wallet, credits
        - Survival tier (normal/low_compute/critical/dead)
        - Last activity, total earnings, total expenses
        """
        
    def calculate_survival_tier(self, conway_credits: float) -> str:
        """
        Calculate survival tier:
        - >= 5000: 'normal'
        - >= 1000: 'low_compute'
        - > 0: 'critical'
        - == 0: 'dead'
        """
        
    async def stop_agent(self, agent_id: str):
        """Stop agent execution and update status to 'paused'"""
        
    async def restart_agent(self, agent_id: str):
        """Restart paused agent if credits > 0"""
```

**Integration Points**:
- Database: `user_automatons` and `automaton_transactions` tables
- Conway Cloud API: `/agents/spawn`, `/agents/status`, `/credits/transfer`
- Railway API: Deployment and environment variable management
- Lineage Manager: Register parent-child relationship after successful spawn (NEW)

### 4. Balance Monitor (`app/balance_monitor.py`)

**Purpose**: Monitors agent Conway credit balances and sends low balance alerts.

**Key Methods**:

```python
class BalanceMonitor:
    async def monitor_low_balances(self):
        """
        Run hourly to check all active agents
        Send alerts when credits < 5000 (warning) or < 1000 (critical)
        """
        
    async def send_low_balance_alert(self, user_id: int, balance: float, 
                                     level: str):
        """
        Send Telegram notification:
        - Critical: < 1 day runtime, urgent deposit needed
        - Warning: < 5 days runtime, deposit recommended
        """
        
    def estimate_runtime(self, conway_credits: float, tier: str) -> float:
        """
        Estimate days of runtime based on credits and tier:
        - Normal: 200 credits/day
        - Low compute: 100 credits/day
        - Critical: 50 credits/day
        """
```

**Alert Thresholds**:
- Critical: < 1000 credits (< 1 day runtime)
- Warning: < 5000 credits (< 5 days runtime)
- Check interval: Every 1 hour

### 5. Revenue Manager (`app/revenue_manager.py`)

**Purpose**: Collects platform fees and tracks revenue metrics.

**Key Methods**:

```python
class RevenueManager:
    def calculate_deposit_fee(self, amount: float) -> tuple[float, float]:
        """
        Calculate 2% deposit fee
        Returns: (net_amount, fee_amount)
        """
        
    async def collect_performance_fee(self, agent_id: str, profit: float):
        """
        Collect 20% performance fee from agent profits:
        1. Calculate 20% of profit
        2. Transfer fee from agent credits
        3. Record transaction
        4. Update platform revenue
        """
        
    def get_revenue_report(self, period: str) -> dict:
        """
        Generate revenue report for period (daily/weekly/monthly):
        - Total deposit fees
        - Total performance fees
        - Revenue by source
        - Top revenue-generating agents
        """
        
    async def record_platform_fee(self, source: str, amount: float, 
                                  agent_id: str = None):
        """Record fee collection in platform_revenue table"""
```

**Fee Structure**:
- Deposit fee: 2% of deposit amount
- Performance fee: 20% of realized profits
- Withdrawal fee: 1 USDT flat fee
- Parent revenue share: 10% of child's gross earnings (NEW)

### 6. Conway Integration (`app/conway_integration.py`)

**Purpose**: Interface with Conway Cloud API for agent runtime management.

**Key Methods**:

```python
class ConwayIntegration:
    def __init__(self):
        """Initialize with Conway API key and base URL"""
        
    async def fund_agent(self, agent_wallet: str, amount: float) -> dict:
        """
        Transfer Conway credits to agent wallet
        POST /credits/transfer
        """
        
    async def check_agent_balance(self, agent_wallet: str) -> dict:
        """
        Query agent's Conway credit balance
        GET /credits/balance
        """
        
    async def spawn_agent_runtime(self, agent_config: dict) -> dict:
        """
        Deploy agent to Conway runtime
        POST /agents/spawn
        """
        
    async def get_agent_logs(self, agent_wallet: str, limit: int = 20) -> list:
        """
        Retrieve agent activity logs
        GET /agents/{wallet}/logs
        """
```

**API Configuration**:
- Base URL: `https://api.conway.tech` (or from `CONWAY_API_URL` env)
- Authentication: Bearer token in `CONWAY_API_KEY` environment variable
- Retry policy: 3 attempts with exponential backoff (1s, 2s, 4s)
- Timeout: 30 seconds per request

### 7. Lineage Manager (`app/lineage_manager.py`) - NEW

**Purpose**: Manages parent-child relationships between agents and handles revenue sharing from children to parents.

**Key Methods**:

```python
class LineageManager:
    def __init__(self):
        """Initialize with database connection"""
        
    async def register_child_agent(self, child_agent_id: str, parent_agent_id: str):
        """
        Register parent-child relationship when spawning from existing agent
        Updates user_automatons.parent_agent_id field
        """
        
    def get_agent_lineage(self, agent_id: str) -> dict:
        """
        Retrieve agent's lineage information:
        - parent_agent_id (if exists)
        - list of child_agent_ids
        - total_children_count
        - total_revenue_from_children
        """
        
    async def distribute_child_revenue(self, child_agent_id: str, child_earnings: float):
        """
        Distribute 10% of child's earnings to parent:
        1. Check if child has parent
        2. Calculate parent share (10% of child_earnings)
        3. Transfer credits from child to parent
        4. Record in lineage_transactions table
        5. Update both agent balances
        6. Notify parent owner
        """
        
    def calculate_parent_share(self, child_earnings: float) -> float:
        """
        Calculate parent's share: child_earnings × 0.10 (10%)
        """
        
    async def get_lineage_tree(self, root_agent_id: str, max_depth: int = 3) -> dict:
        """
        Retrieve hierarchical tree of agent lineage up to max_depth levels
        Returns nested structure with children and their children
        """
        
    def get_lineage_statistics(self, agent_id: str) -> dict:
        """
        Calculate lineage statistics:
        - direct_children_count
        - total_descendants_count (all levels)
        - total_revenue_from_lineage
        - average_child_performance
        """
```

**Revenue Sharing Rules**:
- Parent receives 10% of child's gross earnings (before platform fees)
- Revenue sharing applies to all earning types: trading profits, staking rewards, etc.
- If parent agent is dead (0 credits), revenue still transfers but parent remains inactive
- Revenue sharing is recursive: if A spawns B, and B spawns C, then B gets 10% from C, and A gets 10% from B
- Maximum lineage depth tracked: 10 levels

### 8. Menu Integration (`app/handlers_automaton.py`)

**Purpose**: Telegram bot command and callback handlers for automaton features.

**Key Handlers**:

```python
async def spawn_agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /spawn_agent command or "Spawn Agent" button
    Flow:
    1. Check premium status
    2. Check credit balance
    3. Ask if spawning from existing agent (parent selection)
    4. Confirm spawn with user
    5. Execute spawn via AutomatonManager
    6. If parent selected, register lineage via LineageManager
    7. Send confirmation with agent details
    """

async def agent_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /agent_status command or "Agent Status" button
    Display:
    - Agent name, wallet, credits
    - Survival tier with emoji
    - Parent agent info (if exists)
    - Children count and total revenue from children
    - Last activity, runtime estimate
    - Total earnings, total expenses, net P&L
    """

async def agent_lineage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /agent_lineage command or "Agent Lineage" button (NEW)
    Display:
    - Hierarchical tree of agent's children
    - Each child's status, earnings, and contribution to parent
    - Total descendants count
    - Total revenue from entire lineage
    - Visual tree representation with emojis
    """

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /deposit command or "Fund Agent" button
    Display:
    - Custodial wallet address (monospace)
    - QR code for mobile scanning
    - Supported networks (Polygon, Base, Arbitrum)
    - Conversion rates (1 USDT = 100 credits)
    - Minimum deposit (5 USDT)
    """

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /balance command
    Display:
    - Wallet address
    - USDT/USDC balances
    - Conway credits
    - Total deposited, total spent, net balance
    - Agent survival tier and estimated runtime
    """

async def agent_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /agent_logs command or "Agent Logs" button
    Display last 20 transactions:
    - Type (spawn, fund, earn, spend, fee)
    - Amount (green for earnings, red for expenses)
    - Description
    - Timestamp
    """

async def withdraw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /withdraw <amount> <address> command
    Flow:
    1. Validate amount (min 10 USDT)
    2. Check wallet balance
    3. Create withdrawal request
    4. Deduct 1 USDT fee
    5. Queue for admin processing
    """
```

**Menu Structure**:
```
Main Menu
├── 💰 Market Analysis
├── 📈 Trading Signals
├── 🤖 AI Agent (NEW!)
│   ├── 🚀 Spawn Agent
│   ├── 📊 Agent Status
│   ├── 🌳 Agent Lineage (NEW!)
│   ├── 💰 Fund Agent (Deposit)
│   ├── 📜 Agent Logs
│   └── ⚙️ Agent Settings
│       ├── Enable/Disable Autonomous Spawning (NEW!)
│       └── Set Spawn Strategy (NEW!)
├── 👑 Premium
└── ℹ️ Help
```

### 9. Webhook Handlers (`app/webhook_handlers.py`) - NEW

**Purpose**: Handle callbacks from Conway Cloud for autonomous agent operations.

**Key Endpoints**:

```python
@app.route('/api/agent/autonomous-spawn', methods=['POST'])
async def handle_autonomous_spawn():
    """
    Webhook called by Conway Cloud when agent wants to spawn child
    
    Request Body:
    {
        'parent_agent_id': 'uuid',
        'child_config': {
            'name': 'optional_name',
            'genesis_prompt': 'optional_prompt'
        },
        'signature': 'hmac_signature'
    }
    
    Response:
    {
        'success': true,
        'child_agent_id': 'uuid',
        'child_wallet': '0x...'
    }
    """
    
@app.route('/api/agent/earnings', methods=['POST'])
async def handle_agent_earnings():
    """
    Webhook called by Conway Cloud when agent earns credits
    Triggers lineage revenue distribution
    
    Request Body:
    {
        'agent_id': 'uuid',
        'earnings': 1000.0,
        'source': 'trading_profit',
        'signature': 'hmac_signature'
    }
    """
```

**Security**:
- Verify HMAC signature on all webhook requests
- Use shared secret stored in `CONWAY_WEBHOOK_SECRET` environment variable
- Rate limit webhook endpoints (max 100 requests per minute per agent)
- Log all webhook calls for audit trail

## Data Models

### Database Schema

#### custodial_wallets
```sql
CREATE TABLE custodial_wallets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT REFERENCES users(telegram_id) UNIQUE NOT NULL,
  wallet_address TEXT UNIQUE NOT NULL,
  private_key_encrypted TEXT NOT NULL,
  balance_usdt DECIMAL(18, 6) DEFAULT 0,
  balance_usdc DECIMAL(18, 6) DEFAULT 0,
  conway_credits DECIMAL(18, 2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  last_deposit_at TIMESTAMP,
  total_deposited DECIMAL(18, 6) DEFAULT 0,
  total_spent DECIMAL(18, 6) DEFAULT 0,
  
  CONSTRAINT positive_balances CHECK (
    balance_usdt >= 0 AND 
    balance_usdc >= 0 AND 
    conway_credits >= 0
  )
);

CREATE INDEX idx_custodial_wallet_address ON custodial_wallets(wallet_address);
CREATE INDEX idx_custodial_user_id ON custodial_wallets(user_id);
```

#### wallet_deposits
```sql
CREATE TABLE wallet_deposits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wallet_id UUID REFERENCES custodial_wallets(id) NOT NULL,
  user_id BIGINT REFERENCES users(telegram_id) NOT NULL,
  tx_hash TEXT UNIQUE NOT NULL,
  from_address TEXT NOT NULL,
  amount DECIMAL(18, 6) NOT NULL,
  token TEXT NOT NULL CHECK (token IN ('USDT', 'USDC')),
  network TEXT NOT NULL CHECK (network IN ('polygon', 'base', 'arbitrum')),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'failed')),
  confirmations INT DEFAULT 0,
  detected_at TIMESTAMP DEFAULT NOW(),
  confirmed_at TIMESTAMP,
  credited_conway DECIMAL(18, 2),
  platform_fee DECIMAL(18, 6),
  
  CONSTRAINT positive_amount CHECK (amount > 0)
);

CREATE INDEX idx_deposit_tx_hash ON wallet_deposits(tx_hash);
CREATE INDEX idx_deposit_wallet_id ON wallet_deposits(wallet_id);
CREATE INDEX idx_deposit_status ON wallet_deposits(status);
```

#### wallet_withdrawals
```sql
CREATE TABLE wallet_withdrawals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wallet_id UUID REFERENCES custodial_wallets(id) NOT NULL,
  user_id BIGINT REFERENCES users(telegram_id) NOT NULL,
  amount DECIMAL(18, 6) NOT NULL,
  token TEXT NOT NULL CHECK (token IN ('USDT', 'USDC')),
  to_address TEXT NOT NULL,
  tx_hash TEXT,
  status TEXT DEFAULT 'pending' CHECK (
    status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')
  ),
  requested_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  fee DECIMAL(18, 6) DEFAULT 1.0,
  
  CONSTRAINT positive_amount CHECK (amount >= 10),
  CONSTRAINT valid_address CHECK (to_address ~ '^0x[a-fA-F0-9]{40}$')
);

CREATE INDEX idx_withdrawal_wallet_id ON wallet_withdrawals(wallet_id);
CREATE INDEX idx_withdrawal_status ON wallet_withdrawals(status);
```

#### user_automatons
```sql
CREATE TABLE user_automatons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT REFERENCES users(telegram_id) NOT NULL,
  agent_wallet TEXT UNIQUE NOT NULL,
  agent_name TEXT NOT NULL,
  genesis_prompt TEXT,
  parent_agent_id UUID REFERENCES user_automatons(id), -- NEW: Parent agent reference
  conway_credits DECIMAL(18, 2) DEFAULT 0,
  survival_tier TEXT DEFAULT 'normal' CHECK (
    survival_tier IN ('normal', 'low_compute', 'critical', 'dead')
  ),
  created_at TIMESTAMP DEFAULT NOW(),
  last_active TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'active' CHECK (
    status IN ('active', 'paused', 'dead')
  ),
  total_earnings DECIMAL(18, 6) DEFAULT 0,
  total_expenses DECIMAL(18, 6) DEFAULT 0,
  total_children_revenue DECIMAL(18, 6) DEFAULT 0, -- NEW: Total revenue from children
  autonomous_spawn_enabled BOOLEAN DEFAULT TRUE, -- NEW: Allow agent to spawn children
  last_autonomous_spawn_at TIMESTAMP, -- NEW: Track last autonomous spawn time
  autonomous_spawn_count INT DEFAULT 0, -- NEW: Count of autonomous spawns
  
  CONSTRAINT positive_credits CHECK (conway_credits >= 0)
);

CREATE INDEX idx_automaton_user_id ON user_automatons(user_id);
CREATE INDEX idx_automaton_wallet ON user_automatons(agent_wallet);
CREATE INDEX idx_automaton_status ON user_automatons(status);
CREATE INDEX idx_automaton_parent ON user_automatons(parent_agent_id); -- NEW: Index for lineage queries
CREATE INDEX idx_automaton_autonomous_spawn ON user_automatons(last_autonomous_spawn_at); -- NEW: For rate limiting
```

#### automaton_transactions
```sql
CREATE TABLE automaton_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  automaton_id UUID REFERENCES user_automatons(id) NOT NULL,
  type TEXT NOT NULL CHECK (
    type IN ('spawn', 'fund', 'earn', 'spend', 'performance_fee', 'platform_fee', 'lineage_share')
  ),
  amount DECIMAL(18, 6) NOT NULL,
  description TEXT,
  related_agent_id UUID REFERENCES user_automatons(id), -- NEW: For lineage transactions
  timestamp TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT non_zero_amount CHECK (amount != 0)
);

CREATE INDEX idx_transaction_automaton_id ON automaton_transactions(automaton_id);
CREATE INDEX idx_transaction_type ON automaton_transactions(type);
CREATE INDEX idx_transaction_timestamp ON automaton_transactions(timestamp);
CREATE INDEX idx_transaction_related_agent ON automaton_transactions(related_agent_id); -- NEW
```

#### lineage_transactions (NEW)
```sql
CREATE TABLE lineage_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_agent_id UUID REFERENCES user_automatons(id) NOT NULL,
  child_agent_id UUID REFERENCES user_automatons(id) NOT NULL,
  child_earnings DECIMAL(18, 6) NOT NULL,
  parent_share DECIMAL(18, 6) NOT NULL,
  share_percentage DECIMAL(5, 2) DEFAULT 10.00,
  timestamp TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT positive_amounts CHECK (
    child_earnings > 0 AND 
    parent_share > 0 AND
    parent_share = child_earnings * (share_percentage / 100)
  ),
  CONSTRAINT valid_lineage CHECK (parent_agent_id != child_agent_id)
);

CREATE INDEX idx_lineage_parent ON lineage_transactions(parent_agent_id);
CREATE INDEX idx_lineage_child ON lineage_transactions(child_agent_id);
CREATE INDEX idx_lineage_timestamp ON lineage_transactions(timestamp);
```

#### platform_revenue
```sql
CREATE TABLE platform_revenue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL CHECK (
    source IN ('deposit_fee', 'performance_fee', 'withdrawal_fee')
  ),
  amount DECIMAL(18, 6) NOT NULL,
  agent_id UUID REFERENCES user_automatons(id),
  user_id BIGINT REFERENCES users(telegram_id),
  timestamp TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT positive_amount CHECK (amount > 0)
);

CREATE INDEX idx_revenue_source ON platform_revenue(source);
CREATE INDEX idx_revenue_timestamp ON platform_revenue(timestamp);
CREATE INDEX idx_revenue_agent_id ON platform_revenue(agent_id);
```

### Data Relationships

```
users (existing table)
  ↓ 1:1
custodial_wallets
  ↓ 1:N
wallet_deposits
  
users
  ↓ 1:N
user_automatons
  ↓ 1:N (self-referencing for parent-child) -- NEW
user_automatons
  ↓ 1:N
automaton_transactions

user_automatons
  ↓ 1:N
platform_revenue

user_automatons (parent) -- NEW
  ↓ 1:N
lineage_transactions
  ↓ N:1
user_automatons (child)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies and consolidations:

**Redundant Properties to Consolidate:**
- 3.1 and 3.2 (USDT and USDC conversion rates) → Combine into single property for both tokens
- 16.1, 16.2, 16.3, 16.4 (Survival tier classification) → Combine into single comprehensive tier classification property
- 21.2 and 23.1 (Performance fee calculation) → Same property, consolidate
- 21.4 and 23.4 (Performance fee transaction logging) → Same property, consolidate
- 6.2 and 20.3 (Low balance warning) → Same trigger, consolidate
- 6.3 and 20.4 (Critical balance alert) → Same trigger, consolidate

**Properties Subsumed by Others:**
- 1.3 is subsumed by 1.1 (wallet creation includes database persistence)
- 3.5 is subsumed by 2.4 (credit conversion includes balance update)
- 4.7 is subsumed by 4.3 (spawn process includes database registration)
- 18.3 is subsumed by 4.3 (credit deduction already covered)
- 23.3 is subsumed by 23.2 (balance transfer includes database update)

**Final Property Count:** 45 unique, non-redundant properties

### Correctness Properties

#### Property 1: Unique Wallet Generation
*For any* user ID, generating a custodial wallet should produce a unique, valid Ethereum address (0x followed by 40 hexadecimal characters) that does not collide with any existing wallet address in the system.

**Validates: Requirements 1.1**

#### Property 2: Wallet Encryption Round Trip
*For any* generated wallet private key, encrypting then decrypting using the Fernet cipher should produce the original private key value.

**Validates: Requirements 1.2, 11.1**

#### Property 3: One Wallet Per User Invariant
*For any* user, creating multiple automatons should always return the same custodial wallet address, ensuring exactly one wallet per user regardless of the number of agents spawned.

**Validates: Requirements 1.4**

#### Property 4: Deposit Address Response Completeness
*For any* deposit address request, the response should contain the wallet address, a valid QR code URL, and a list of supported networks (Polygon, Base, Arbitrum).

**Validates: Requirements 1.5**

#### Property 5: Deposit Detection and Recording
*For any* detected USDT or USDC deposit to a custodial wallet, a record should be created in the wallet_deposits table with status 'pending' and the correct amount, token, and network.

**Validates: Requirements 2.2**

#### Property 6: Confirmation Status Transition
*For any* deposit with 12 or more blockchain confirmations, the status in wallet_deposits table should be 'confirmed'.

**Validates: Requirements 2.3, 15.5**

#### Property 7: Conway Credits Conversion Formula
*For any* confirmed deposit of amount A in USDT or USDC, the credited Conway credits should equal (A × 0.98) × 100, where 0.98 represents the 2% platform fee deduction.

**Validates: Requirements 2.4, 3.1, 3.2, 3.3, 21.1**

#### Property 8: Minimum Deposit Validation
*For any* deposit amount less than 5 USDT or 5 USDC, the deposit should be rejected and the user should receive a notification about the minimum requirement.

**Validates: Requirements 3.4**

#### Property 9: Premium Access Control for Spawning
*For any* user with is_premium = 0 or FALSE, attempting to spawn an agent should be rejected with a message to upgrade to premium.

**Validates: Requirements 4.1, 17.2**

#### Property 10: Spawn Credit Balance Validation
*For any* user with credits < 100,000, attempting to spawn an agent should be rejected with a message showing current balance and required amount.

**Validates: Requirements 4.2, 18.2**

#### Property 11: Spawn Fee Deduction
*For any* successful agent spawn, the user's credit balance should decrease by exactly 100,000 credits.

**Validates: Requirements 4.3, 18.3**

#### Property 12: Agent Wallet Uniqueness
*For any* spawned agent, the generated agent_wallet address should be unique across all agents and be a valid Ethereum address format.

**Validates: Requirements 4.4**

#### Property 13: Spawn Confirmation Notification
*For any* successfully spawned agent, a Telegram notification should be sent containing the agent name, wallet address, initial credits, and status.

**Validates: Requirements 4.8, 20.2**

#### Property 14: Agent Status Retrieval
*For any* existing agent ID, requesting agent status should return a record containing agent_name, agent_wallet, conway_credits, survival_tier, last_active, total_earnings, and total_expenses.

**Validates: Requirements 5.1, 5.2**

#### Property 15: Survival Tier Classification
*For any* Conway credit balance C, the survival tier should be: 'dead' if C = 0, 'critical' if 0 < C < 1000, 'low_compute' if 1000 ≤ C < 5000, 'normal' if C ≥ 5000.

**Validates: Requirements 5.3, 16.1, 16.2, 16.3, 16.4**

#### Property 16: Runtime Estimation
*For any* agent with Conway credits C and survival tier T, the estimated runtime in days should be C / R where R is the consumption rate (200 for normal, 100 for low_compute, 50 for critical).

**Validates: Requirements 5.4**

#### Property 17: Transaction Aggregation
*For any* agent, the total_earnings should equal the sum of all automaton_transactions with type 'earn', and total_expenses should equal the sum of all transactions with type 'spend' plus Conway credit consumption.

**Validates: Requirements 5.5, 22.3, 22.4**

#### Property 18: Low Balance Warning Trigger
*For any* active agent with 1000 ≤ conway_credits < 5000, a warning notification should be sent to the user containing current balance, estimated runtime, and deposit recommendation.

**Validates: Requirements 6.3, 20.3**

#### Property 19: Critical Balance Alert Trigger
*For any* active agent with 0 < conway_credits < 1000, a critical alert should be sent to the user containing current balance, estimated runtime (< 1 day), and urgent deposit instructions.

**Validates: Requirements 6.2, 20.4**

#### Property 20: Alert Message Completeness
*For any* low balance alert (warning or critical), the message should contain the current balance, estimated runtime in days, and instructions for depositing funds.

**Validates: Requirements 6.4, 6.5**

#### Property 21: QR Code Generation
*For any* custodial wallet address, the deposit display should include a valid QR code URL in the format `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={address}`.

**Validates: Requirements 8.2**

#### Property 22: Transaction Log Limiting
*For any* agent logs request, the returned transactions should be limited to at most 20 records, ordered by timestamp descending.

**Validates: Requirements 9.1**

#### Property 23: Transaction Record Completeness
*For any* transaction in the agent logs, the record should contain type, amount, description, and timestamp fields.

**Validates: Requirements 9.2**

#### Property 24: Admin Wallet Aggregation
*For any* admin wallet summary request, the total USDT balance should equal the sum of balance_usdt across all custodial_wallets, and total USDC should equal the sum of balance_usdc.

**Validates: Requirements 10.1**

#### Property 25: Platform Revenue Calculation
*For any* set of custodial wallets, the platform revenue should equal the sum of all records in platform_revenue table, which should match 2% of total deposits plus 20% of total agent profits.

**Validates: Requirements 10.3**

#### Property 26: Survival Rate Calculation
*For any* set of agents, the survival rate percentage should equal (count of agents with status 'active') / (total count of agents) × 100.

**Validates: Requirements 10.4**

#### Property 27: Audit Logging for Decryption
*For any* private key decryption operation, an audit log entry should be created with the timestamp, wallet address, and operation type.

**Validates: Requirements 11.4**

#### Property 28: Withdrawal Balance Validation
*For any* withdrawal request with amount A, if the user's balance_usdt < A, the withdrawal should be rejected with an insufficient balance message.

**Validates: Requirements 12.1**

#### Property 29: Minimum Withdrawal Validation
*For any* withdrawal request with amount < 10 USDT, the request should be rejected with a message about the 10 USDT minimum.

**Validates: Requirements 12.2**

#### Property 30: Withdrawal Fee Deduction
*For any* withdrawal request of amount A, the net withdrawal amount should be A - 1 USDT (flat fee).

**Validates: Requirements 12.3**

#### Property 31: Withdrawal Request Persistence
*For any* created withdrawal request, a record should exist in wallet_withdrawals table with status 'pending', the requested amount, to_address, and timestamp.

**Validates: Requirements 12.4**

#### Property 32: Withdrawal Status Transition
*For any* processed withdrawal, the status should be updated to 'completed' and the tx_hash field should contain a valid Ethereum transaction hash.

**Validates: Requirements 12.5**

#### Property 33: Conway API Credit Transfer
*For any* agent funding operation, the Conway Cloud API /credits/transfer endpoint should be called with the correct agent_wallet and credit amount in the request body.

**Validates: Requirements 13.1**

#### Property 34: Conway API Balance Check
*For any* agent balance query, the Conway Cloud API /credits/balance endpoint should be called with the agent_wallet as a query parameter.

**Validates: Requirements 13.2**

#### Property 35: Conway API Authentication
*For any* Conway Cloud API request, the Authorization header should contain "Bearer {CONWAY_API_KEY}" where the API key is retrieved from environment variables.

**Validates: Requirements 13.3**

#### Property 36: API Retry Logic
*For any* failed Conway API call, the system should retry the request up to 3 times with exponential backoff (1s, 2s, 4s) before considering it a permanent failure.

**Validates: Requirements 13.4, 23.5**

#### Property 37: API Failure Notification
*For any* Conway API call that fails after 3 retry attempts, an error should be logged and an admin notification should be sent via Telegram.

**Validates: Requirements 13.5**

#### Property 38: ERC20 Balance Query
*For any* custodial wallet address, checking the token balance should call the ERC20 contract's balanceOf function with the wallet address as the parameter.

**Validates: Requirements 15.4**

#### Property 39: Dead Agent Operation Prevention
*For any* agent with survival_tier = 'dead' (conway_credits = 0), all agent operations (trading, analysis, etc.) should be rejected until credits are added.

**Validates: Requirements 16.5**

#### Property 40: Premium Status Query
*For any* spawn attempt, the system should query the users table for the is_premium column to verify premium status before proceeding.

**Validates: Requirements 17.1, 18.1**

#### Property 41: Expired Premium Agent Persistence
*For any* agent belonging to a user whose premium subscription has expired, the agent should continue running (not automatically stopped) but the user should be prevented from spawning new agents.

**Validates: Requirements 17.4, 17.5**

#### Property 42: Spawn Activity Logging
*For any* successful credit deduction for spawning, a record should be created in user_activity table with action 'agent_spawned' and the user_id.

**Validates: Requirements 18.4**

#### Property 43: Spawn Failure Refund
*For any* spawn process that fails after credits have been deducted, the 100,000 credits should be refunded to the user's account.

**Validates: Requirements 18.5**

#### Property 44: Deposit Confirmation Notification
*For any* confirmed deposit, a Telegram notification should be sent containing the deposit amount, token type (USDT/USDC), and the credited Conway credits amount.

**Validates: Requirements 20.1**

#### Property 45: Dead Agent Notification
*For any* agent that reaches conway_credits = 0, a notification should be sent to the user indicating the agent is now in 'dead' status and requires funding to restart.

**Validates: Requirements 20.5**

#### Property 46: Performance Fee Calculation
*For any* agent that realizes a profit P (closed position with positive P&L), the platform should collect a performance fee of P × 0.20 (20%).

**Validates: Requirements 21.2, 21.3, 23.1**

#### Property 47: Performance Fee Transaction Logging
*For any* collected performance fee, two transaction records should be created: one in automaton_transactions with type 'performance_fee' and one in platform_revenue with source 'performance_fee'.

**Validates: Requirements 21.4, 21.5, 23.4**

#### Property 48: Performance Fee Balance Transfer
*For any* performance fee F collected from an agent, the agent's conway_credits should decrease by F and the platform_revenue total should increase by F.

**Validates: Requirements 23.2**

#### Property 49: Profit Transaction Recording
*For any* agent that closes a profitable trade with profit P, a record should be created in automaton_transactions with type 'earn' and amount P.

**Validates: Requirements 22.1**

#### Property 50: Loss Transaction Recording
*For any* agent that closes a losing trade with loss L, a record should be created in automaton_transactions with type 'spend' and amount L.

**Validates: Requirements 22.2**

#### Property 51: Net Profit Calculation
*For any* agent, the displayed net profit/loss should equal total_earnings - total_expenses, where earnings are the sum of 'earn' transactions and expenses are the sum of 'spend' transactions plus Conway credit consumption.

**Validates: Requirements 22.5**

#### Property 52: Revenue Report Aggregation
*For any* revenue report request, the total deposit fees should equal the sum of all platform_revenue records with source 'deposit_fee', and total performance fees should equal the sum of records with source 'performance_fee'.

**Validates: Requirements 24.1, 24.2**

#### Property 53: Time-Based Revenue Breakdown
*For any* revenue report with period P (daily/weekly/monthly), the revenue should be grouped by timestamp within the period boundaries and summed for each time bucket.

**Validates: Requirements 24.3**

#### Property 54: Revenue Source Breakdown
*For any* revenue report, the revenue should be grouped by the source column (deposit_fee, performance_fee, withdrawal_fee) and summed for each source type.

**Validates: Requirements 24.4**

#### Property 55: Top Revenue Agents
*For any* revenue report, the top 10 agents should be determined by summing all platform_revenue records grouped by agent_id, sorted descending by total revenue, and limited to 10 results.

**Validates: Requirements 24.5**

---

### Parent-Child Lineage Properties (NEW)

#### Property 56: Parent Agent Registration
*For any* agent spawn operation with a specified parent_agent_id, the spawned agent's parent_agent_id field should be set to the specified parent, and the parent must be an existing, valid agent.

**Validates: Requirements 25.1**

#### Property 57: Parent Share Calculation
*For any* child agent earnings E, the parent's share should equal E × 0.10 (10% of child's gross earnings).

**Validates: Requirements 25.2**

#### Property 58: Lineage Revenue Transfer
*For any* child agent that earns amount E, if the child has a parent, the parent's conway_credits should increase by E × 0.10 and the child's conway_credits should decrease by E × 0.10.

**Validates: Requirements 25.3**

#### Property 59: Lineage Transaction Recording
*For any* parent revenue share transfer, a record should be created in lineage_transactions table with parent_agent_id, child_agent_id, child_earnings, parent_share (10%), and timestamp.

**Validates: Requirements 25.4**

#### Property 60: Parent Share Constraint
*For any* lineage transaction, the parent_share amount must equal child_earnings × (share_percentage / 100), and share_percentage must be 10.00.

**Validates: Requirements 25.5**

#### Property 61: Lineage Transaction Dual Recording
*For any* parent revenue share, two transaction records should be created: one in automaton_transactions for the child (type 'lineage_share', negative amount) and one for the parent (type 'lineage_share', positive amount).

**Validates: Requirements 25.6**

#### Property 62: Total Children Revenue Accumulation
*For any* parent agent, the total_children_revenue field should equal the sum of all lineage_transactions.parent_share where parent_agent_id matches the agent.

**Validates: Requirements 25.7**

#### Property 63: Lineage Tree Depth Limit
*For any* lineage tree query, the returned tree structure should not exceed the specified max_depth parameter (default 3, maximum 10 levels).

**Validates: Requirements 25.8**

#### Property 64: Circular Lineage Prevention
*For any* agent spawn with parent specification, the system should reject the spawn if it would create a circular reference (e.g., agent A cannot be parent of agent B if B is already an ancestor of A).

**Validates: Requirements 25.9**

#### Property 65: Dead Parent Revenue Acceptance
*For any* parent agent with survival_tier = 'dead' (conway_credits = 0), the agent should still receive revenue shares from children, increasing its conway_credits balance.

**Validates: Requirements 25.10**

#### Property 66: Lineage Statistics Accuracy
*For any* agent, the lineage statistics should accurately reflect: direct_children_count (count of agents with this agent as parent_agent_id), total_descendants_count (recursive count of all descendants), and total_revenue_from_lineage (sum of all lineage_transactions.parent_share).

**Validates: Requirements 25.11**

#### Property 67: Parent Notification on Revenue Share
*For any* lineage revenue transfer, a Telegram notification should be sent to the parent agent's owner containing the child agent name, earnings amount, and parent's share received.

**Validates: Requirements 25.12**

#### Property 68: Recursive Revenue Sharing
*For any* multi-level lineage (A spawns B, B spawns C), when C earns amount E, B should receive E × 0.10, and A should receive (B's earnings) × 0.10, demonstrating recursive revenue sharing.

**Validates: Requirements 25.13**

#### Property 69: Lineage Query Performance
*For any* lineage tree query with depth D and N total descendants, the query should complete in O(N) time complexity using indexed parent_agent_id lookups.

**Validates: Requirements 25.14**

#### Property 70: Agent Status Lineage Display
*For any* agent status query, if the agent has a parent, the response should include parent_agent_id, parent_name, and if the agent has children, it should include children_count and total_children_revenue.

**Validates: Requirements 25.15**

---

### Autonomous Spawning Properties (NEW)

#### Property 71: Autonomous Spawn Credit Validation
*For any* autonomous spawn request from an agent, the spawn should only proceed if the agent's conway_credits >= 100,000.

**Validates: Requirements 26.1**

#### Property 72: Autonomous Spawn Rate Limiting
*For any* agent, autonomous spawns should be limited to maximum 1 spawn per 24 hours, enforced by checking last_autonomous_spawn_at timestamp.

**Validates: Requirements 26.2**

#### Property 73: Autonomous Spawn Enabled Check
*For any* autonomous spawn request, the spawn should only proceed if the agent's autonomous_spawn_enabled field is TRUE.

**Validates: Requirements 26.3**

#### Property 74: Autonomous Spawn Credit Deduction
*For any* successful autonomous spawn, the parent agent's conway_credits should decrease by exactly 100,000 and a transaction record with type 'spawn' should be created.

**Validates: Requirements 26.4**

#### Property 75: Autonomous Spawn Parent Linkage
*For any* autonomously spawned child agent, the child's parent_agent_id should be set to the spawning agent's ID, and the child's user_id should match the parent's user_id.

**Validates: Requirements 26.5**

#### Property 76: Autonomous Spawn Notification
*For any* successful autonomous spawn, a Telegram notification should be sent to the user containing the parent agent name, child agent name, and child wallet address.

**Validates: Requirements 26.6**

#### Property 77: Autonomous Spawn Counter Increment
*For any* successful autonomous spawn, the parent agent's autonomous_spawn_count should increment by 1, and last_autonomous_spawn_at should be updated to current timestamp.

**Validates: Requirements 26.7**

#### Property 78: Webhook Signature Verification
*For any* webhook request from Conway Cloud (autonomous spawn or earnings), the request should be rejected if the HMAC signature does not match the expected signature using CONWAY_WEBHOOK_SECRET.

**Validates: Requirements 26.8**

#### Property 79: Autonomous Spawn Depth Limit
*For any* autonomous spawn request, the spawn should be rejected if the resulting lineage depth would exceed 10 levels.

**Validates: Requirements 26.9**

#### Property 80: Autonomous Spawn Inheritance
*For any* autonomously spawned child, if no custom genesis_prompt is provided, the child should inherit the parent's genesis_prompt.

**Validates: Requirements 26.10**

## Error Handling

### Error Categories and Recovery Strategies

#### 1. Wallet Generation Errors
**Scenarios:**
- Encryption key not found in environment
- Database insertion failure
- Duplicate wallet address (extremely rare)

**Recovery:**
- Log error with full context
- Notify admin via Telegram
- Return user-friendly error message
- Do not proceed with spawn

#### 2. Blockchain Interaction Errors
**Scenarios:**
- RPC node unavailable
- Network timeout
- Invalid contract address
- Gas estimation failure

**Recovery:**
- Retry with exponential backoff (3 attempts)
- Fall back to alternative RPC endpoint if available
- Log error for monitoring
- Continue monitoring on next cycle

#### 3. Conway API Errors
**Scenarios:**
- API key invalid or expired
- Rate limit exceeded
- Service unavailable
- Invalid request parameters

**Recovery:**
- Retry with exponential backoff (1s, 2s, 4s)
- Log error with request/response details
- Notify admin after 3 failed attempts
- Queue operation for manual review

#### 4. Database Errors
**Scenarios:**
- Connection timeout
- Constraint violation
- Deadlock
- Disk full

**Recovery:**
- Rollback transaction immediately
- Retry operation once after 1 second
- Log error with query details
- Return generic error to user
- Alert admin for persistent failures

#### 5. Deposit Processing Errors
**Scenarios:**
- Deposit below minimum
- Unsupported token
- Failed credit conversion
- Notification delivery failure

**Recovery:**
- Mark deposit as 'failed' in database
- Log reason for failure
- Notify user if possible
- Admin can manually process if needed

#### 6. Spawn Process Errors
**Scenarios:**
- Insufficient credits after verification
- Railway deployment failure
- Database registration failure
- Conway provisioning failure

**Recovery:**
- Refund spawn fee (100,000 credits)
- Log error at each step
- Notify user of failure with reason
- Admin can retry manually

#### 7. Performance Fee Collection Errors
**Scenarios:**
- Agent balance insufficient for fee
- Conway API transfer failure
- Database update failure

**Recovery:**
- Retry fee collection on next profit event
- Log failed collection attempt
- Do not block agent operation
- Admin dashboard shows pending fees

### Error Response Format

All error responses to users follow this format:
```
❌ **Error: {Error Type}**

{User-friendly description}

💡 **What to do:**
{Actionable steps}

🆔 Error ID: {UUID for support reference}
```

### Monitoring and Alerting

**Critical Errors (Immediate Admin Alert):**
- Wallet encryption key missing
- Database connection lost
- Conway API authentication failure
- Multiple spawn failures

**Warning Errors (Hourly Digest):**
- Individual deposit detection failures
- Single API retry exhaustion
- Notification delivery failures

**Info Errors (Daily Report):**
- Below minimum deposit attempts
- Non-premium spawn attempts
- Insufficient credit spawn attempts

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific examples and edge cases
- Integration points between components
- Error conditions and recovery
- Database schema validation
- API contract verification

**Property-Based Tests** focus on:
- Universal properties across all inputs
- Invariants that must always hold
- Mathematical correctness (fees, conversions)
- State transitions and consistency
- Comprehensive input coverage through randomization

Together, unit tests catch concrete bugs while property tests verify general correctness.

### Property-Based Testing Configuration

**Framework:** Use `hypothesis` for Python property-based testing

**Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each test must reference its design document property
- Tag format: `# Feature: automaton-integration, Property {number}: {property_text}`

**Example Property Test:**
```python
from hypothesis import given, strategies as st
import pytest

# Feature: automaton-integration, Property 7: Conway Credits Conversion Formula
@given(deposit_amount=st.floats(min_value=5.0, max_value=10000.0))
def test_conway_credits_conversion(deposit_amount):
    """
    For any confirmed deposit of amount A in USDT or USDC,
    the credited Conway credits should equal (A × 0.98) × 100
    """
    expected_credits = (deposit_amount * 0.98) * 100
    actual_credits = calculate_conway_credits(deposit_amount)
    
    assert abs(actual_credits - expected_credits) < 0.01  # Allow for floating point precision
```

### Unit Testing Strategy

**Test Organization:**
```
tests/
├── unit/
│   ├── test_wallet_manager.py
│   ├── test_deposit_monitor.py
│   ├── test_automaton_manager.py
│   ├── test_balance_monitor.py
│   ├── test_revenue_manager.py
│   └── test_conway_integration.py
├── integration/
│   ├── test_spawn_workflow.py
│   ├── test_deposit_workflow.py
│   ├── test_fee_collection.py
│   └── test_notification_delivery.py
└── property/
    ├── test_wallet_properties.py
    ├── test_conversion_properties.py
    ├── test_fee_properties.py
    └── test_aggregation_properties.py
```

**Key Unit Test Cases:**

1. **Wallet Manager:**
   - Generate wallet with valid format
   - Encrypt/decrypt round trip
   - One wallet per user enforcement
   - Handle encryption key missing

2. **Deposit Monitor:**
   - Detect USDT deposit on Polygon
   - Detect USDC deposit on Polygon
   - Wait for 12 confirmations
   - Handle RPC node failure
   - Process multiple deposits concurrently

3. **Automaton Manager:**
   - Spawn with sufficient credits
   - Reject spawn without premium
   - Reject spawn with insufficient credits
   - Refund on spawn failure
   - Calculate survival tiers correctly

4. **Balance Monitor:**
   - Send warning at 5000 credits
   - Send critical alert at 1000 credits
   - No alert for dead agents (0 credits)
   - Estimate runtime correctly

5. **Revenue Manager:**
   - Calculate 2% deposit fee
   - Calculate 20% performance fee
   - Aggregate revenue by source
   - Generate time-based reports

6. **Lineage Manager (NEW):**
   - Register parent-child relationship
   - Calculate 10% parent share
   - Transfer credits from child to parent
   - Prevent circular lineage
   - Query lineage tree with depth limit
   - Calculate lineage statistics

### Integration Testing

**Critical Workflows to Test:**

1. **End-to-End Spawn:**
   - User clicks spawn button
   - Premium verified
   - Credits deducted
   - Wallet generated
   - Agent deployed
   - Database updated
   - User notified

2. **End-to-End Deposit:**
   - User deposits USDT
   - Monitor detects deposit
   - Wait for confirmations
   - Calculate Conway credits
   - Credit via Conway API
   - Update database
   - Notify user

3. **End-to-End Fee Collection:**
   - Agent makes profit
   - Calculate 20% fee
   - Transfer from agent
   - Record in transactions
   - Update revenue table
   - Update agent balance

4. **End-to-End Lineage Revenue Sharing (NEW):**
   - Child agent earns profit
   - Calculate 10% parent share
   - Transfer from child to parent
   - Record in lineage_transactions
   - Update both agent balances
   - Notify parent owner
   - Verify recursive sharing (grandparent gets share from parent's earnings)

### Mocking Strategy

**External Services to Mock:**
- Conway Cloud API (all endpoints)
- Polygon RPC node (Web3 calls)
- Telegram Bot API (notifications)
- Railway API (deployments)

**Mock Libraries:**
- `unittest.mock` for Python mocking
- `responses` for HTTP mocking
- `pytest-mock` for pytest integration

### Test Data Generation

**Use Hypothesis strategies for:**
- Random user IDs (1000000 to 9999999)
- Random deposit amounts (5.0 to 10000.0)
- Random credit balances (0 to 1000000)
- Random Ethereum addresses
- Random timestamps
- Random lineage depths (1 to 10) (NEW)
- Random parent-child relationships (NEW)

**Fixed test data for:**
- Known premium users
- Known wallet addresses
- Known transaction hashes
- Known agent configurations
- Known lineage hierarchies (NEW)

### Coverage Goals

- **Line Coverage:** Minimum 85%
- **Branch Coverage:** Minimum 80%
- **Property Coverage:** 100% of correctness properties tested
- **Integration Coverage:** All critical workflows tested

### Continuous Testing

**Pre-commit:**
- Run unit tests
- Run linting (flake8, black)
- Check type hints (mypy)

**CI Pipeline:**
- Run all unit tests
- Run all property tests (100 iterations)
- Run integration tests
- Generate coverage report
- Fail if coverage < 85%

**Nightly:**
- Run property tests (1000 iterations)
- Run load tests
- Run security scans
- Generate comprehensive report

---

## Deployment Considerations

### Environment Variables

Required environment variables for Railway deployment:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=<bot_token>

# Database
SUPABASE_URL=<supabase_url>
SUPABASE_KEY=<supabase_anon_key>
SUPABASE_SERVICE_KEY=<supabase_service_role_key>

# Blockchain
POLYGON_RPC_URL=<polygon_rpc_url>
WALLET_ENCRYPTION_KEY=<fernet_key_base64>

# Conway Cloud
CONWAY_API_URL=https://api.conway.tech
CONWAY_API_KEY=<conway_api_key>

# Admin
ADMIN_IDS=<comma_separated_admin_telegram_ids>
```

### Database Migrations

Migration scripts should be created for:
1. Create custodial_wallets table
2. Create wallet_deposits table
3. Create wallet_withdrawals table
4. Create user_automatons table
5. Create automaton_transactions table
6. Create platform_revenue table
7. Add indexes for performance

### Background Services

Services that need to run continuously:
1. **Deposit Monitor** - Every 30 seconds
2. **Balance Monitor** - Every 1 hour
3. **Performance Fee Collector** - Every 5 minutes
4. **Health Check** - Every 1 minute

Use Python `asyncio` with separate tasks for each service.

### Monitoring and Observability

**Metrics to Track:**
- Deposit detection latency
- Conway API response time
- Spawn success rate
- Agent survival rate
- Platform revenue (real-time)
- Error rates by category

**Logging:**
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include request IDs for tracing
- Sensitive data (private keys) never logged

### Security Checklist

- [ ] Master encryption key stored in Railway secrets
- [ ] Private keys never logged or exposed
- [ ] API keys rotated every 90 days
- [ ] Database uses parameterized queries (no SQL injection)
- [ ] Input validation on all user inputs
- [ ] Rate limiting on spawn operations
- [ ] Admin commands restricted by telegram ID
- [ ] Audit logging for all sensitive operations
- [ ] Regular security audits scheduled

### Rollback Plan

If critical issues are discovered:
1. Disable spawn functionality via feature flag
2. Stop deposit monitor to prevent new deposits
3. Notify all users of maintenance
4. Fix issues in staging environment
5. Test thoroughly with property tests
6. Re-enable features gradually
7. Monitor closely for 24 hours

---

## Parent-Child Lineage Architecture (NEW)

### Overview

The parent-child lineage system enables agents to spawn new agents, creating a hierarchical tree structure where parent agents receive 10% of their children's earnings. This creates a sustainable incentive for users to grow their agent networks and rewards successful agent strategies through passive income from descendants.

### Key Design Principles

1. **Recursive Revenue Sharing**: Revenue flows up the lineage tree - if A spawns B and B spawns C, then B gets 10% from C, and A gets 10% from B's earnings
2. **No Capital Lock**: Parent agents don't need to fund children - each agent operates independently
3. **Passive Income**: Parent owners earn from children's success without active management
4. **Lineage Transparency**: Users can view their entire agent family tree and revenue contributions
5. **Performance Incentive**: Successful agent strategies naturally propagate through spawning
6. **Autonomous Expansion**: Agents can autonomously spawn children when they have sufficient credits (NEW)
7. **Self-Sustaining Networks**: Successful agents can build their own agent networks without user intervention (NEW)

### Autonomous Spawning Mechanism (NEW)

Agents running on Conway Cloud can autonomously decide to spawn child agents based on their programming and available credits. This creates a self-expanding network of agents.

**How It Works:**

1. **Agent Decision Making**: 
   - Agent analyzes its performance and credit balance
   - If credits >= 100,000 and strategy indicates spawning is beneficial
   - Agent initiates spawn request to Conway Cloud API

2. **Spawn Execution**:
   - Conway Cloud calls bot's webhook: `/api/agent/autonomous-spawn`
   - Bot validates parent agent and deducts 100,000 credits
   - New child agent is created with parent_agent_id set
   - Child inherits parent's genesis_prompt (or modified version)
   - Child starts with 0 credits (parent can fund later)

3. **User Notification**:
   - User receives Telegram notification about autonomous spawn
   - Notification includes parent name, child name, and child wallet
   - User can view lineage tree to see new child

4. **Revenue Flow**:
   - When child earns, parent automatically receives 10%
   - Parent can use earnings to fund child or spawn more children
   - Creates self-sustaining agent ecosystem

**Example Scenario:**

```
Day 1: User spawns Agent Alpha (100k credits)
Day 5: Alpha earns 150k credits from trading
Day 7: Alpha autonomously spawns Agent Beta (Alpha now has 50k credits)
Day 10: User deposits 100k credits to Alpha
Day 12: Alpha funds Beta with 50k credits
Day 15: Beta starts earning, Alpha receives 10% automatically
Day 20: Beta has 120k credits, spawns Agent Gamma autonomously
Day 25: Gamma earns → Beta gets 10% → Alpha gets 10% of Beta's earnings
```

**Benefits:**

- **Exponential Growth**: Successful agents can build networks without user intervention
- **Passive Scaling**: Users benefit from agent networks growing automatically
- **Strategy Propagation**: Successful trading strategies spread through lineage
- **Reduced Management**: Agents manage their own expansion
- **Increased Revenue**: More agents = more revenue sharing opportunities

### Lineage Revenue Flow

```
                    Grandparent Agent (A)
                           ↑
                    10% of B's earnings
                           │
                    Parent Agent (B)
                           ↑
                    10% of C's earnings
                           │
                    Child Agent (C)
                           │
                    Earns 1000 credits
                           
Revenue Distribution:
1. C earns 1000 credits (gross)
2. Platform takes 20% performance fee = 200 credits
3. C's net earnings = 800 credits
4. B (parent) receives 10% of C's gross = 100 credits
5. C keeps 700 credits
6. When B earns (including the 100 from C), A receives 10% of B's earnings
```

### Lineage Constraints

**Maximum Depth**: 10 levels
- Prevents infinite recursion
- Ensures query performance
- Limits complexity for users

**No Circular References**:
- Agent A cannot be parent of agent B if B is ancestor of A
- Validated at spawn time
- Prevents infinite loops in revenue distribution

**Parent Must Exist**:
- parent_agent_id must reference valid agent
- Parent can be in any status (active, paused, dead)
- Dead parents still receive revenue shares

### Lineage Operations

#### 1. Spawn with Parent (User-Initiated)

```python
# User manually spawns new agent from existing agent
async def spawn_child_agent(user_id, parent_agent_id, name, genesis_prompt):
    # 1. Verify parent exists and belongs to user
    parent = get_agent(parent_agent_id)
    if not parent or parent.user_id != user_id:
        raise InvalidParentError()
    
    # 2. Check for circular reference
    if would_create_cycle(parent_agent_id, user_id):
        raise CircularLineageError()
    
    # 3. Spawn agent normally
    child = await spawn_agent(user_id, name, genesis_prompt)
    
    # 4. Register lineage
    await lineage_manager.register_child_agent(
        child_agent_id=child.id,
        parent_agent_id=parent_agent_id
    )
    
    return child
```

#### 1b. Autonomous Child Spawning (Agent-Initiated) - NEW

```python
# Agent autonomously spawns child when it has sufficient credits
async def agent_autonomous_spawn(parent_agent_id, child_config):
    """
    Called by Conway Cloud when agent decides to spawn child
    This happens when:
    - Agent has >= 100,000 credits
    - Agent's strategy determines spawning is beneficial
    - Agent has been programmed/trained to spawn children
    """
    # 1. Verify parent agent exists and has credits
    parent = get_agent(parent_agent_id)
    if not parent:
        raise AgentNotFoundError()
    
    if parent.conway_credits < 100000:
        raise InsufficientCreditsError()
    
    # 2. Deduct spawn cost from parent agent
    await deduct_credits(parent_agent_id, 100000)
    
    # 3. Generate child agent configuration
    child_name = child_config.get('name') or f"{parent.agent_name}-Child-{timestamp}"
    child_prompt = child_config.get('genesis_prompt') or parent.genesis_prompt
    
    # 4. Create child agent wallet
    child_wallet = generate_agent_wallet()
    
    # 5. Deploy child to Conway Cloud
    child_agent = await conway_integration.spawn_agent_runtime({
        'wallet': child_wallet,
        'name': child_name,
        'genesis_prompt': child_prompt,
        'initial_credits': 0  # Parent can fund later
    })
    
    # 6. Register in database with parent reference
    child_id = await db.insert_agent({
        'user_id': parent.user_id,  # Same owner as parent
        'agent_wallet': child_wallet,
        'agent_name': child_name,
        'genesis_prompt': child_prompt,
        'parent_agent_id': parent_agent_id,  # Link to parent
        'conway_credits': 0,
        'status': 'active'
    })
    
    # 7. Record spawn transaction for parent
    await record_transaction(
        parent_agent_id,
        'spawn',
        -100000,
        f"Spawned child agent: {child_name}"
    )
    
    # 8. Notify user about autonomous spawn
    await notify_user_autonomous_spawn(
        user_id=parent.user_id,
        parent_name=parent.agent_name,
        child_name=child_name,
        child_wallet=child_wallet
    )
    
    return child_id
```

#### 2. Distribute Child Revenue

```python
# Called whenever child agent earns
async def on_agent_earnings(agent_id, earnings_amount):
    # 1. Record earnings
    await record_transaction(agent_id, 'earn', earnings_amount)
    
    # 2. Check if agent has parent
    agent = get_agent(agent_id)
    if not agent.parent_agent_id:
        return  # No parent, done
    
    # 3. Calculate parent share (10%)
    parent_share = earnings_amount * 0.10
    
    # 4. Transfer credits
    await transfer_credits(
        from_agent=agent_id,
        to_agent=agent.parent_agent_id,
        amount=parent_share
    )
    
    # 5. Record lineage transaction
    await record_lineage_transaction(
        parent_agent_id=agent.parent_agent_id,
        child_agent_id=agent_id,
        child_earnings=earnings_amount,
        parent_share=parent_share
    )
    
    # 6. Update parent's total_children_revenue
    await increment_children_revenue(
        agent.parent_agent_id,
        parent_share
    )
    
    # 7. Notify parent owner
    await notify_parent_revenue(
        agent.parent_agent_id,
        child_name=agent.name,
        earnings=earnings_amount,
        share=parent_share
    )
    
    # 8. Recursive: parent's earnings trigger grandparent share
    await on_agent_earnings(agent.parent_agent_id, parent_share)
```

#### 3. Query Lineage Tree

```python
# Retrieve hierarchical tree structure
async def get_lineage_tree(root_agent_id, max_depth=3):
    """
    Returns nested structure:
    {
        'agent_id': 'uuid',
        'name': 'Agent Alpha',
        'credits': 50000,
        'total_children_revenue': 5000,
        'children': [
            {
                'agent_id': 'uuid',
                'name': 'Agent Beta',
                'credits': 30000,
                'total_children_revenue': 1000,
                'children': [...]
            }
        ]
    }
    """
    return await build_tree_recursive(root_agent_id, max_depth, current_depth=0)
```

### Lineage Statistics

For each agent, track:

1. **Direct Children Count**: Number of agents with this agent as parent
2. **Total Descendants**: Recursive count of all children, grandchildren, etc.
3. **Total Revenue from Lineage**: Sum of all lineage_transactions.parent_share
4. **Average Child Performance**: Mean earnings of direct children
5. **Lineage Depth**: Maximum depth of descendant tree

### User Interface

#### Agent Status Display

```
🤖 Agent Status: Alpha Trader

📊 Performance:
├─ Credits: 50,000 Conway
├─ Survival: 🟢 Normal (250 days)
├─ Total Earnings: 100,000 credits
└─ Total Expenses: 50,000 credits

🌳 Lineage:
├─ Parent: Beta Master (ID: abc123)
├─ Children: 5 agents
├─ Total Descendants: 12 agents
└─ Revenue from Children: 5,000 credits

💰 Net P&L: +50,000 credits
```

#### Lineage Tree Display

```
🌳 Agent Lineage Tree

Alpha Trader (You)
├─ 📊 50,000 credits
├─ 💰 5,000 from children
│
├─ 🤖 Beta Agent
│   ├─ 📊 30,000 credits
│   ├─ 💰 1,000 from children
│   │
│   ├─ 🤖 Gamma Agent
│   │   └─ 📊 10,000 credits
│   │
│   └─ 🤖 Delta Agent
│       └─ 📊 15,000 credits
│
└─ 🤖 Epsilon Agent
    └─ 📊 25,000 credits

Total Lineage Revenue: 5,000 credits
Total Descendants: 4 agents
```

### Performance Considerations

**Database Queries**:
- Use indexed parent_agent_id for fast lookups
- Limit tree depth to prevent expensive recursive queries
- Cache lineage statistics for frequently accessed agents

**Revenue Distribution**:
- Process asynchronously to avoid blocking agent operations
- Batch multiple revenue shares if possible
- Retry failed transfers with exponential backoff

**Notification Throttling**:
- Group multiple small revenue shares into periodic summaries
- Only notify for shares above threshold (e.g., 10 credits)
- Daily digest for users with many children

### Security Considerations

**Lineage Validation**:
- Verify parent ownership before spawning
- Prevent cross-user lineage (agent A owned by user X cannot be parent of agent B owned by user Y)
- Validate lineage depth limits

**Revenue Protection**:
- Ensure child has sufficient credits before transfer
- Rollback on transfer failure
- Audit all lineage transactions

**Anti-Abuse**:
- Rate limit spawn operations (max 10 spawns per agent per day)
- Monitor for suspicious lineage patterns
- Alert on deep lineage trees (> 5 levels)
- Prevent spawn loops (agent cannot spawn if it would exceed depth limit)

**Autonomous Spawn Controls (NEW)**:
- Verify agent has minimum 100,000 credits before autonomous spawn
- Rate limit autonomous spawns (max 1 per agent per 24 hours)
- Monitor for spawn spam (alert if agent spawns > 5 children in 7 days)
- User can disable autonomous spawning per agent via settings
- Admin can globally disable autonomous spawning if abuse detected
- Log all autonomous spawn events for audit trail

---

**Design Status:** Complete and ready for implementation
**Next Step:** Create implementation tasks (tasks.md)
