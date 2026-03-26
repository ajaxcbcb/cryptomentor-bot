# Design Document: Dual-Mode Offline-Online Bot System

## Overview

The dual-mode system provides users with two distinct operational modes for the CryptoMentor Telegram bot:

1. **Offline Mode**: Manual trading features using Binance API without LLM processing
2. **Online Mode**: AI-powered trading with isolated Automaton agents using LLM

This design enables users to choose between cost-effective manual analysis and premium AI-assisted trading based on their needs and available Automaton credits. The system ensures smooth transitions between modes while maintaining data integrity and user context.

### Key Design Goals

- Clear separation between offline (manual) and online (AI) functionality
- Seamless mode switching with preserved user state
- Isolated AI agents per user for fair resource allocation
- Credit-based access control for online mode
- Graceful error handling and fallback mechanisms
- Transparent UI/UX that clearly indicates active mode

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot Layer                       │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ Command      │              │ Message      │            │
│  │ Handlers     │              │ Handlers     │            │
│  └──────┬───────┘              └──────┬───────┘            │
└─────────┼──────────────────────────────┼──────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Mode Manager Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Mode State Manager                                   │  │
│  │  - Track user mode (offline/online)                  │  │
│  │  - Handle mode transitions                           │  │
│  │  - Validate mode access                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────┬───────────────┘
          │                                   │
          ▼                                   ▼
┌──────────────────────┐          ┌──────────────────────────┐
│   Offline Mode       │          │    Online Mode           │
│   Handler            │          │    Handler               │
│                      │          │                          │
│  - Technical         │          │  - Session Manager       │
│    Analysis          │          │  - AI Agent Manager      │
│  - Futures Signals   │          │  - Credit Manager        │
│  - Binance API       │          │  - Automaton Bridge      │
│    Integration       │          │                          │
│  - No LLM            │          │  - LLM Integration       │
└──────────┬───────────┘          └──────────┬───────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐          ┌──────────────────────────┐
│   Binance API        │          │   Automaton API          │
│   - Market Data      │          │   - AI Agent Instances   │
│   - Price Feeds      │          │   - Genesis Prompt       │
│   - Technical        │          │   - Credit Tracking      │
│     Indicators       │          │   - Conversation History │
└──────────────────────┘          └──────────────────────────┘
```

### Component Interaction Flow

**Offline Mode Flow:**
```
User → /offline → Mode Manager → Offline Handler → Binance API → Response
```

**Online Mode Flow:**
```
User → /online → Mode Manager → Credit Check → Session Manager → 
AI Agent → Automaton API → LLM → Response → Credit Deduction
```


## Components and Interfaces

### 1. Mode State Manager

**Responsibility**: Track and manage user mode state across sessions

**Interface**:
```python
class ModeStateManager:
    def get_user_mode(user_id: int) -> str
    def set_user_mode(user_id: int, mode: str) -> bool
    def is_offline_mode(user_id: int) -> bool
    def is_online_mode(user_id: int) -> bool
    def transition_mode(user_id: int, from_mode: str, to_mode: str) -> TransitionResult
    def get_mode_history(user_id: int, limit: int = 10) -> List[ModeTransition]
```

**Data Model**:
```python
@dataclass
class UserModeState:
    user_id: int
    current_mode: str  # 'offline' | 'online'
    previous_mode: Optional[str]
    last_transition: datetime
    transition_count: int
    offline_state: Optional[Dict]  # Preserved offline context
    online_session_id: Optional[str]  # Active online session
```

**Storage**: Supabase table `user_mode_states`

### 2. Offline Mode Handler

**Responsibility**: Process manual trading requests without LLM

**Interface**:
```python
class OfflineModeHandler:
    def handle_analyze_command(user_id: int, symbol: str) -> AnalysisResult
    def handle_futures_command(user_id: int, symbol: str, timeframe: str) -> SignalResult
    def handle_manual_signal(user_id: int, params: Dict) -> SignalResult
    def get_offline_menu() -> InlineKeyboardMarkup
    def format_offline_response(data: Dict) -> str
```

**Features**:
- Technical analysis using Binance market data
- Futures signal generation
- SMC (Smart Money Concepts) analysis
- No LLM processing (cost-effective)
- Response prefix: `[OFFLINE] 📊`

### 3. Online Mode Handler

**Responsibility**: Manage AI-powered trading interactions

**Interface**:
```python
class OnlineModeHandler:
    def activate_online_mode(user_id: int) -> ActivationResult
    def deactivate_online_mode(user_id: int) -> bool
    def handle_user_message(user_id: int, message: str) -> AIResponse
    def get_online_menu() -> InlineKeyboardMarkup
    def format_online_response(data: Dict, credits_remaining: int) -> str
```

**Features**:
- Isolated AI agent per user
- Natural language processing
- Conversational trading assistance
- Automated signal generation
- Credit-based usage
- Response prefix: `[ONLINE - AI] 🤖`

### 4. Session Manager

**Responsibility**: Manage isolated AI agent sessions

**Interface**:
```python
class SessionManager:
    def create_session(user_id: int) -> Session
    def get_session(user_id: int) -> Optional[Session]
    def close_session(user_id: int) -> bool
    def is_session_active(user_id: int) -> bool
    def update_session_activity(user_id: int) -> bool
```

**Data Model**:
```python
@dataclass
class Session:
    session_id: str
    user_id: int
    agent_id: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    credits_used: int
    status: str  # 'active' | 'closed' | 'expired'
```

**Storage**: Supabase table `online_sessions`

### 5. AI Agent Manager

**Responsibility**: Manage isolated AI agent instances

**Interface**:
```python
class AIAgentManager:
    def get_or_create_agent(user_id: int) -> Agent
    def get_agent(user_id: int) -> Optional[Agent]
    def initialize_agent(user_id: int, genesis_prompt: str) -> Agent
    def delete_agent(user_id: int) -> bool
    def is_agent_isolated(agent_id: str, user_id: int) -> bool
```

**Data Model**:
```python
@dataclass
class Agent:
    agent_id: str
    user_id: int
    genesis_prompt: str
    conversation_history: List[Message]
    created_at: datetime
    last_used: datetime
    total_messages: int
    status: str  # 'active' | 'inactive' | 'deleted'
```

**Storage**: Supabase table `isolated_ai_agents`


### 6. Credit Manager

**Responsibility**: Track and manage Automaton credits

**Interface**:
```python
class CreditManager:
    def get_user_credits(user_id: int) -> int
    def has_sufficient_credits(user_id: int, required: int) -> bool
    def deduct_credits(user_id: int, amount: int, reason: str) -> bool
    def add_credits(user_id: int, amount: int, reason: str) -> bool
    def get_credit_history(user_id: int, limit: int = 20) -> List[CreditTransaction]
    def validate_admin_balance(admin_id: int, amount: int) -> ValidationResult
```

**Data Model**:
```python
@dataclass
class CreditTransaction:
    transaction_id: str
    user_id: int
    amount: int  # Positive for additions, negative for deductions
    balance_after: int
    reason: str
    timestamp: datetime
    admin_id: Optional[int]  # If admin-initiated
```

**Storage**: Supabase table `automaton_credit_transactions`

### 7. Automaton Bridge

**Responsibility**: Interface with Automaton API for AI agent operations

**Interface**:
```python
class AutomatonBridge:
    def send_message(agent_id: str, message: str) -> AutomatonResponse
    def get_agent_status(agent_id: str) -> AgentStatus
    def validate_api_connection() -> bool
    def get_admin_balance(admin_id: int) -> int
    def deduct_admin_credits(admin_id: int, amount: int) -> bool
    def retry_with_backoff(operation: Callable, max_retries: int = 3) -> Any
```

**Configuration**:
```python
AUTOMATON_CONFIG = {
    'api_url': os.getenv('AUTOMATON_API_URL'),
    'api_key': os.getenv('AUTOMATON_API_KEY'),
    'timeout': 30,  # seconds
    'max_retries': 3,
    'backoff_factor': 2  # exponential backoff
}
```

### 8. Genesis Prompt Loader

**Responsibility**: Load and manage Genesis Prompt configuration

**Interface**:
```python
class GenesisPromptLoader:
    def load_prompt() -> str
    def reload_prompt() -> str
    def get_current_prompt() -> str
    def update_prompt(new_prompt: str) -> bool
    def get_prompt_version() -> str
```

**Storage**: File-based (`AUTOMATON_GENESIS_PROMPT.md`) with in-memory caching

## Data Models

### Database Schema

**Table: user_mode_states**
```sql
CREATE TABLE user_mode_states (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    current_mode VARCHAR(20) NOT NULL CHECK (current_mode IN ('offline', 'online')),
    previous_mode VARCHAR(20),
    last_transition TIMESTAMP NOT NULL DEFAULT NOW(),
    transition_count INTEGER NOT NULL DEFAULT 0,
    offline_state JSONB,
    online_session_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_mode_states_user_id ON user_mode_states(user_id);
CREATE INDEX idx_user_mode_states_current_mode ON user_mode_states(current_mode);
```

**Table: online_sessions**
```sql
CREATE TABLE online_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMP NOT NULL DEFAULT NOW(),
    message_count INTEGER NOT NULL DEFAULT 0,
    credits_used INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed', 'expired')),
    closed_at TIMESTAMP
);

CREATE INDEX idx_online_sessions_user_id ON online_sessions(user_id);
CREATE INDEX idx_online_sessions_status ON online_sessions(status);
CREATE INDEX idx_online_sessions_agent_id ON online_sessions(agent_id);
```

**Table: isolated_ai_agents**
```sql
CREATE TABLE isolated_ai_agents (
    agent_id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    genesis_prompt TEXT NOT NULL,
    conversation_history JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used TIMESTAMP NOT NULL DEFAULT NOW(),
    total_messages INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deleted'))
);

CREATE INDEX idx_isolated_ai_agents_user_id ON isolated_ai_agents(user_id);
CREATE INDEX idx_isolated_ai_agents_status ON isolated_ai_agents(status);
```

**Table: automaton_credit_transactions**
```sql
CREATE TABLE automaton_credit_transactions (
    transaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    reason VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    admin_id BIGINT,
    session_id UUID REFERENCES online_sessions(session_id)
);

CREATE INDEX idx_credit_transactions_user_id ON automaton_credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_timestamp ON automaton_credit_transactions(timestamp DESC);
CREATE INDEX idx_credit_transactions_admin_id ON automaton_credit_transactions(admin_id);
```

**Table: mode_transition_log**
```sql
CREATE TABLE mode_transition_log (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    from_mode VARCHAR(20),
    to_mode VARCHAR(20) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_mode_transition_log_user_id ON mode_transition_log(user_id);
CREATE INDEX idx_mode_transition_log_timestamp ON mode_transition_log(timestamp DESC);
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following consolidations to eliminate redundancy:

**Consolidated Properties:**
- Properties 1.3, 1.4, 1.5, 1.6 → Combined into Property 1: Mode activation with credit validation
- Properties 2.1, 2.2 → Combined into Property 2: Offline mode feature access
- Properties 3.1, 3.2 → Combined into Property 3: Online mode initialization
- Properties 3.3, 3.8, 3.9 → Combined into Property 4: Online mode message handling with credit management
- Properties 4.2, 4.4, 4.6 → Combined into Property 5: Credit tracking and logging
- Properties 6.3, 6.4, 6.5, 6.6 → Combined into Property 6: Admin credit grant flow
- Properties 7.1, 7.2, 7.3, 7.4 → Combined into Property 7: AI agent transaction processing
- Properties 8.2, 8.3, 8.5, 8.6 → Combined into Property 8: Mode-specific UI presentation
- Properties 9.1, 9.2, 9.3 → Combined into Property 9: State preservation during transitions
- Properties 10.1, 10.2, 10.3, 10.4, 10.5 → Combined into Property 10: Agent isolation
- Properties 11.2, 11.5, 11.6 → Combined into Property 11: Genesis Prompt injection
- Properties 12.1, 12.2, 12.3 → Combined into Property 12: Error handling with retry logic
- Properties 13.1, 13.3, 13.5, 13.10 → Combined into Property 13: Automaton API credit validation

This consolidation reduces 80+ individual criteria into 20 comprehensive properties that provide unique validation value without logical redundancy.

### Property 1: Mode Activation with Credit Validation

*For any* user attempting to activate online mode, the system should check their Automaton credits, and if sufficient credits exist, activate online mode and create a session; otherwise, display instructions for obtaining credits.

**Validates: Requirements 1.3, 1.4, 1.5, 1.6**

### Property 2: Offline Mode Feature Access

*For any* user in offline mode, all manual trading features (technical analysis, futures signals) should be accessible using Binance API without LLM processing.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 3: Online Mode Initialization

*For any* user activating online mode for the first time, the system should create a new isolated session and initialize their personal AI agent with the Genesis Prompt.

**Validates: Requirements 3.1, 3.2**

### Property 4: Online Mode Message Handling with Credit Management

*For any* message sent by a user in online mode, the system should forward it to their isolated AI agent, deduct credits based on usage, and display remaining credits after the interaction.

**Validates: Requirements 3.3, 3.8, 3.9**

### Property 5: Credit Tracking and Logging

*For any* Automaton credit transaction (addition or deduction), the system should persist the transaction to the database with timestamp, amount, reason, and updated balance.

**Validates: Requirements 4.2, 4.4, 4.6**

### Property 6: Admin Credit Grant Flow

*For any* admin credit grant operation, the system should prompt for user ID and amount, validate the inputs, add credits to the user's account, send confirmation to admin, and notify the user.

**Validates: Requirements 6.3, 6.4, 6.5, 6.6**

### Property 7: AI Agent Transaction Processing

*For any* deposit or withdrawal request made in online mode, the AI agent should process the request conversationally, provide appropriate instructions or validation, log the transaction, and send confirmation to the user.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6, 7.7**

### Property 8: Mode-Specific UI Presentation

*For any* response in a given mode, the system should display the appropriate mode prefix ([OFFLINE] or [ONLINE - AI]), use mode-specific emojis, show the corresponding menu, and include a welcome message when switching modes.

**Validates: Requirements 8.2, 8.3, 8.5, 8.6**

### Property 9: State Preservation During Transitions

*For any* mode transition, the system should preserve the previous mode's state, gracefully close any active sessions, maintain user data integrity, and complete the transition without data loss.

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 10: Agent Isolation

*For any* two distinct users, their AI agents should be completely isolated such that user A cannot access user B's agent, conversation history, or session data.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

### Property 11: Genesis Prompt Injection

*For any* newly created AI agent, the system should inject the current Genesis Prompt as the system prompt, ensuring all agents have consistent base knowledge for trading operations.

**Validates: Requirements 11.2, 11.5, 11.6**

### Property 12: Error Handling with Retry Logic

*For any* AI agent failure, the system should retry up to 3 times with exponential backoff, and if all retries fail, display an informative error message without deducting credits.

**Validates: Requirements 12.2, 12.3**

### Property 13: Automaton API Credit Validation

*For any* admin credit grant operation, the system should validate the Automaton API connection, check the admin's available balance, ensure the grant amount does not exceed the balance, and deduct from the admin's balance upon successful grant.

**Validates: Requirements 13.1, 13.2, 13.3, 13.5, 13.10**

### Property 14: Mode Persistence

*For any* mode change, the system should persist the new mode state to the database and increment the transition counter.

**Validates: Requirements 1.7**

### Property 15: Mode Transition Performance

*For any* mode transition, the system should complete the operation within 2 seconds and display a loading indicator during the transition.

**Validates: Requirements 9.4, 9.5**

### Property 16: Transition Error Recovery

*For any* error during mode transition, the system should display an error message, keep the user in their previous mode, and log the failed transition.

**Validates: Requirements 9.6, 9.7**

### Property 17: First Deposit Auto-Activation

*For any* user's first successful deposit, the system should automatically activate online mode and direct the user to their AI agent.

**Validates: Requirements 5.6**

### Property 18: Audit Logging

*For any* admin action, the system should create an audit log entry with user ID, action type, timestamp, and relevant details.

**Validates: Requirements 6.7**

### Property 19: Automaton Service Fallback

*For any* Automaton service unavailability, the system should display an error message suggesting offline mode as an alternative.

**Validates: Requirements 12.1**

### Property 20: Critical Error Notification

*For any* critical error in online mode, the system should log detailed error information and send a notification to the admin.

**Validates: Requirements 12.4, 12.5**


## Error Handling

### Error Categories

**1. Mode Transition Errors**
- Invalid mode specified
- Insufficient credits for online mode
- Session creation failure
- Database persistence failure

**Handling Strategy**:
```python
try:
    result = transition_mode(user_id, from_mode, to_mode)
    if not result.success:
        # Keep user in previous mode
        send_error_message(user_id, result.error)
        log_failed_transition(user_id, from_mode, to_mode, result.error)
except Exception as e:
    # Fallback to safe state
    set_user_mode(user_id, 'offline')  # Default to offline
    notify_admin_critical_error(user_id, e)
```

**2. Automaton API Errors**
- Connection timeout
- API unavailable
- Authentication failure
- Rate limit exceeded

**Handling Strategy**:
```python
def call_automaton_api_with_retry(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except TimeoutError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                # All retries failed
                return ErrorResponse(
                    message="Automaton service unavailable. Try offline mode.",
                    suggest_offline=True
                )
        except AuthenticationError:
            # Don't retry auth errors
            notify_admin_auth_failure()
            return ErrorResponse(message="Authentication failed. Contact admin.")
```

**3. Credit Management Errors**
- Insufficient credits
- Invalid credit amount
- Transaction failure
- Admin balance exceeded

**Handling Strategy**:
```python
def deduct_credits_safe(user_id, amount, reason):
    try:
        current_balance = get_user_credits(user_id)
        if current_balance < amount:
            return CreditResult(
                success=False,
                error="Insufficient credits",
                current_balance=current_balance,
                required=amount
            )
        
        # Atomic transaction
        with db.transaction():
            new_balance = current_balance - amount
            update_user_credits(user_id, new_balance)
            log_credit_transaction(user_id, -amount, new_balance, reason)
        
        return CreditResult(success=True, new_balance=new_balance)
    except Exception as e:
        log_error("Credit deduction failed", user_id, e)
        return CreditResult(success=False, error=str(e))
```

**4. Agent Isolation Errors**
- Agent not found
- Agent belongs to different user
- Session expired
- Conversation history corruption

**Handling Strategy**:
```python
def get_user_agent_safe(user_id, agent_id):
    agent = get_agent(agent_id)
    if not agent:
        return AgentResult(error="Agent not found")
    
    if agent.user_id != user_id:
        log_security_violation(user_id, agent_id)
        notify_admin_security_issue(user_id, agent_id)
        return AgentResult(error="Access denied")
    
    return AgentResult(success=True, agent=agent)
```

**5. Database Errors**
- Connection failure
- Query timeout
- Constraint violation
- Data corruption

**Handling Strategy**:
```python
def handle_database_error(operation, fallback_cache=True):
    try:
        return operation()
    except DatabaseConnectionError:
        if fallback_cache:
            # Use local cache for read operations
            return get_from_cache()
        else:
            return ErrorResponse(
                message="Database temporarily unavailable. Try again later."
            )
    except QueryTimeoutError:
        log_slow_query(operation)
        return ErrorResponse(message="Operation timed out. Try again.")
```

### Error Response Format

All error responses follow a consistent format:

```python
@dataclass
class ErrorResponse:
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict] = None
    suggested_action: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

### User-Facing Error Messages

**Offline Mode Errors**:
- "❌ Technical analysis failed. Please try again."
- "❌ Invalid symbol. Use format: BTCUSDT"
- "❌ Binance API temporarily unavailable. Try again in a moment."

**Online Mode Errors**:
- "❌ Insufficient Automaton credits. Use /credits to check balance."
- "❌ AI agent unavailable. Switching to offline mode."
- "❌ Session expired. Use /online to start a new session."

**Admin Errors**:
- "❌ Invalid user ID. Please check and try again."
- "❌ Insufficient admin balance. Available: X credits, Requested: Y credits."
- "❌ Automaton API connection failed. Check API credentials."

### Logging Strategy

**Log Levels**:
- `DEBUG`: Mode transitions, session creation
- `INFO`: Successful operations, credit transactions
- `WARNING`: Retry attempts, fallback activations
- `ERROR`: Failed operations, API errors
- `CRITICAL`: Security violations, data corruption

**Log Format**:
```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "ERROR",
    "component": "OnlineModeHandler",
    "user_id": 12345,
    "operation": "activate_online_mode",
    "error": "Automaton API timeout",
    "details": {
        "attempt": 3,
        "duration_ms": 30000
    }
}
```


## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points
**Property Tests**: Verify universal properties across all inputs with randomization

### Unit Testing

**Test Categories**:

1. **Command Handler Tests**
   - `/offline` command activates offline mode
   - `/online` command checks credits before activation
   - `/credits` command displays current balance
   - `/status` command shows active mode and system health
   - Invalid commands return appropriate error messages

2. **Mode Transition Tests**
   - Offline → Online transition with sufficient credits
   - Offline → Online transition with insufficient credits
   - Online → Offline transition closes session gracefully
   - Rapid mode switching maintains data integrity
   - Transition during active operation completes safely

3. **Credit Management Tests**
   - Credit deduction after online mode message
   - Credit addition by admin
   - Insufficient credit handling
   - Credit transaction logging
   - Admin balance validation

4. **UI/UX Tests**
   - Offline mode shows [OFFLINE] prefix
   - Online mode shows [ONLINE - AI] prefix
   - Mode-specific menus display correctly
   - Welcome messages appear on mode switch
   - Loading indicators during transitions

5. **Error Handling Tests**
   - Automaton API timeout triggers retry
   - Failed retry shows error without credit deduction
   - Database failure uses cache fallback
   - Invalid user ID shows clear error
   - Critical errors notify admin

6. **Integration Tests**
   - End-to-end offline mode flow
   - End-to-end online mode flow
   - Admin credit grant flow
   - First deposit auto-activation
   - Agent isolation between users

### Property-Based Testing

**Configuration**: Minimum 100 iterations per property test

**Property Test 1: Mode Activation Credit Validation**
```python
@given(
    user_id=st.integers(min_value=1, max_value=999999),
    credits=st.integers(min_value=0, max_value=100000)
)
def test_online_mode_activation_requires_credits(user_id, credits):
    """
    Feature: dual-mode-offline-online, Property 1:
    For any user attempting to activate online mode, the system should 
    check their Automaton credits, and if sufficient credits exist, 
    activate online mode and create a session; otherwise, display 
    instructions for obtaining credits.
    """
    set_user_credits(user_id, credits)
    result = activate_online_mode(user_id)
    
    if credits >= MINIMUM_CREDITS_REQUIRED:
        assert result.success
        assert result.session_id is not None
        assert get_user_mode(user_id) == 'online'
    else:
        assert not result.success
        assert "obtain credits" in result.message.lower()
        assert get_user_mode(user_id) != 'online'
```

**Property Test 2: Offline Mode Feature Access**
```python
@given(
    user_id=st.integers(min_value=1, max_value=999999),
    symbol=st.sampled_from(['BTCUSDT', 'ETHUSDT', 'BNBUSDT']),
    timeframe=st.sampled_from(['1h', '4h', '1d'])
)
def test_offline_mode_no_llm_usage(user_id, symbol, timeframe):
    """
    Feature: dual-mode-offline-online, Property 2:
    For any user in offline mode, all manual trading features should be 
    accessible using Binance API without LLM processing.
    """
    set_user_mode(user_id, 'offline')
    
    with mock.patch('llm_client.call') as mock_llm:
        result = handle_analyze_command(user_id, symbol)
        assert result.success
        assert mock_llm.call_count == 0  # No LLM calls
        
        result = handle_futures_command(user_id, symbol, timeframe)
        assert result.success
        assert mock_llm.call_count == 0  # No LLM calls
```

**Property Test 3: Online Mode Initialization**
```python
@given(user_id=st.integers(min_value=1, max_value=999999))
def test_online_mode_creates_isolated_agent(user_id):
    """
    Feature: dual-mode-offline-online, Property 3:
    For any user activating online mode for the first time, the system 
    should create a new isolated session and initialize their personal 
    AI agent with the Genesis Prompt.
    """
    # Ensure user has no existing agent
    delete_agent_if_exists(user_id)
    set_user_credits(user_id, 10000)
    
    result = activate_online_mode(user_id)
    
    assert result.success
    assert result.session_id is not None
    
    agent = get_agent(user_id)
    assert agent is not None
    assert agent.user_id == user_id
    assert GENESIS_PROMPT_CONTENT in agent.genesis_prompt
```

**Property Test 4: Credit Deduction on Message**
```python
@given(
    user_id=st.integers(min_value=1, max_value=999999),
    initial_credits=st.integers(min_value=100, max_value=10000),
    message=st.text(min_size=1, max_size=500)
)
def test_online_mode_deducts_credits(user_id, initial_credits, message):
    """
    Feature: dual-mode-offline-online, Property 4:
    For any message sent by a user in online mode, the system should 
    forward it to their isolated AI agent, deduct credits based on usage, 
    and display remaining credits after the interaction.
    """
    set_user_credits(user_id, initial_credits)
    set_user_mode(user_id, 'online')
    create_session(user_id)
    
    response = handle_user_message(user_id, message)
    
    assert response.success
    final_credits = get_user_credits(user_id)
    assert final_credits < initial_credits  # Credits deducted
    assert response.credits_remaining == final_credits
```

**Property Test 5: Credit Transaction Logging**
```python
@given(
    user_id=st.integers(min_value=1, max_value=999999),
    amount=st.integers(min_value=-1000, max_value=1000),
    reason=st.text(min_size=1, max_size=100)
)
def test_credit_transactions_are_logged(user_id, amount, reason):
    """
    Feature: dual-mode-offline-online, Property 5:
    For any Automaton credit transaction, the system should persist 
    the transaction to the database with timestamp, amount, reason, 
    and updated balance.
    """
    initial_balance = get_user_credits(user_id)
    
    if amount > 0:
        add_credits(user_id, amount, reason)
    else:
        deduct_credits(user_id, abs(amount), reason)
    
    transactions = get_credit_history(user_id, limit=1)
    assert len(transactions) > 0
    
    latest = transactions[0]
    assert latest.user_id == user_id
    assert latest.amount == amount
    assert latest.reason == reason
    assert latest.timestamp is not None
    assert latest.balance_after == get_user_credits(user_id)
```

**Property Test 6: Agent Isolation**
```python
@given(
    user_a=st.integers(min_value=1, max_value=999999),
    user_b=st.integers(min_value=1, max_value=999999)
)
def test_agents_are_isolated_between_users(user_a, user_b):
    """
    Feature: dual-mode-offline-online, Property 10:
    For any two distinct users, their AI agents should be completely 
    isolated such that user A cannot access user B's agent, conversation 
    history, or session data.
    """
    assume(user_a != user_b)
    
    # Create agents for both users
    set_user_credits(user_a, 10000)
    set_user_credits(user_b, 10000)
    activate_online_mode(user_a)
    activate_online_mode(user_b)
    
    agent_a = get_agent(user_a)
    agent_b = get_agent(user_b)
    
    # Verify isolation
    assert agent_a.agent_id != agent_b.agent_id
    assert agent_a.user_id == user_a
    assert agent_b.user_id == user_b
    
    # User A cannot access User B's agent
    result = get_user_agent_safe(user_a, agent_b.agent_id)
    assert not result.success
    assert "access denied" in result.error.lower()
```

**Property Test 7: State Preservation During Transitions**
```python
@given(
    user_id=st.integers(min_value=1, max_value=999999),
    offline_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.text(min_size=1, max_size=100)
    )
)
def test_mode_transition_preserves_state(user_id, offline_data):
    """
    Feature: dual-mode-offline-online, Property 9:
    For any mode transition, the system should preserve the previous 
    mode's state, gracefully close any active sessions, maintain user 
    data integrity, and complete the transition without data loss.
    """
    # Set up offline mode with state
    set_user_mode(user_id, 'offline')
    save_offline_state(user_id, offline_data)
    
    # Transition to online
    set_user_credits(user_id, 10000)
    result = transition_mode(user_id, 'offline', 'online')
    
    assert result.success
    assert get_user_mode(user_id) == 'online'
    
    # Verify offline state preserved
    preserved_state = get_offline_state(user_id)
    assert preserved_state == offline_data
    
    # Transition back to offline
    result = transition_mode(user_id, 'online', 'offline')
    
    assert result.success
    assert get_user_mode(user_id) == 'offline'
    
    # Verify state still intact
    final_state = get_offline_state(user_id)
    assert final_state == offline_data
```

**Property Test 8: Retry Logic with Exponential Backoff**
```python
@given(
    user_id=st.integers(min_value=1, max_value=999999),
    failure_count=st.integers(min_value=1, max_value=5)
)
def test_retry_logic_with_backoff(user_id, failure_count):
    """
    Feature: dual-mode-offline-online, Property 12:
    For any AI agent failure, the system should retry up to 3 times 
    with exponential backoff, and if all retries fail, display an 
    informative error message without deducting credits.
    """
    set_user_mode(user_id, 'online')
    initial_credits = 10000
    set_user_credits(user_id, initial_credits)
    
    with mock.patch('automaton_api.send_message') as mock_api:
        # Simulate failures
        mock_api.side_effect = [TimeoutError()] * failure_count + [{"response": "success"}]
        
        result = handle_user_message(user_id, "test message")
        
        if failure_count <= 3:
            # Should succeed after retries
            assert result.success
            assert mock_api.call_count == failure_count + 1
        else:
            # Should fail after 3 retries
            assert not result.success
            assert mock_api.call_count == 3
            assert "unavailable" in result.error.lower()
            
            # Credits should not be deducted on failure
            assert get_user_credits(user_id) == initial_credits
```

### Test Coverage Goals

- **Line Coverage**: > 90%
- **Branch Coverage**: > 85%
- **Property Test Iterations**: 100 per property
- **Integration Test Scenarios**: All critical user flows
- **Error Path Coverage**: All error handlers tested

### Continuous Integration

All tests run automatically on:
- Pull request creation
- Merge to main branch
- Nightly builds

**CI Pipeline**:
```yaml
test:
  - unit_tests: pytest tests/unit/
  - property_tests: pytest tests/property/ --hypothesis-iterations=100
  - integration_tests: pytest tests/integration/
  - coverage_report: pytest --cov=app --cov-report=html
```


## Implementation Notes

### Phase 1: Core Infrastructure (Priority: High)

**Tasks**:
1. Create database schema (tables: user_mode_states, online_sessions, isolated_ai_agents, automaton_credit_transactions, mode_transition_log)
2. Implement ModeStateManager class
3. Implement CreditManager class
4. Add mode tracking to user context

**Dependencies**: Supabase database access

**Estimated Effort**: 3-4 days

### Phase 2: Offline Mode Handler (Priority: High)

**Tasks**:
1. Implement OfflineModeHandler class
2. Create offline mode menu structure
3. Integrate existing manual signal handlers
4. Add [OFFLINE] prefix to responses
5. Ensure no LLM calls in offline mode

**Dependencies**: Phase 1, existing Binance API integration

**Estimated Effort**: 2-3 days

### Phase 3: Online Mode Handler (Priority: High)

**Tasks**:
1. Implement OnlineModeHandler class
2. Implement SessionManager class
3. Implement AIAgentManager class
4. Create online mode menu structure
5. Add [ONLINE - AI] prefix to responses
6. Integrate credit deduction logic

**Dependencies**: Phase 1, Automaton API access

**Estimated Effort**: 4-5 days

### Phase 4: Automaton Integration (Priority: High)

**Tasks**:
1. Implement AutomatonBridge class
2. Add retry logic with exponential backoff
3. Implement Genesis Prompt loader
4. Test API connection and error handling
5. Validate admin balance checking

**Dependencies**: Phase 3, Automaton API credentials

**Estimated Effort**: 3-4 days

### Phase 5: Command Handlers (Priority: Medium)

**Tasks**:
1. Implement /offline command
2. Implement /online command
3. Implement /credits command
4. Implement /status command
5. Update /admin command for credit management
6. Add mode-aware message routing

**Dependencies**: Phases 2, 3, 4

**Estimated Effort**: 2-3 days

### Phase 6: UI/UX Polish (Priority: Medium)

**Tasks**:
1. Design mode-specific emojis and icons
2. Create welcome messages for each mode
3. Add loading indicators for transitions
4. Implement mode-specific menus
5. Add visual distinction between modes

**Dependencies**: Phase 5

**Estimated Effort**: 2 days

### Phase 7: Error Handling (Priority: High)

**Tasks**:
1. Implement comprehensive error handlers
2. Add fallback mechanisms
3. Implement admin notification system
4. Add detailed logging
5. Test all error paths

**Dependencies**: All previous phases

**Estimated Effort**: 3 days

### Phase 8: Testing (Priority: High)

**Tasks**:
1. Write unit tests for all components
2. Write property-based tests (20 properties)
3. Write integration tests for critical flows
4. Perform load testing
5. Security testing for agent isolation

**Dependencies**: All previous phases

**Estimated Effort**: 5-6 days

### Phase 9: Documentation and Deployment (Priority: Medium)

**Tasks**:
1. Write user documentation
2. Write admin documentation
3. Create deployment guide
4. Perform staging deployment
5. Production deployment with monitoring

**Dependencies**: Phase 8

**Estimated Effort**: 2-3 days

**Total Estimated Effort**: 26-33 days

### Technology Stack

**Backend**:
- Python 3.10+
- python-telegram-bot library
- Supabase (PostgreSQL)
- Automaton API client

**Testing**:
- pytest for unit tests
- Hypothesis for property-based testing
- pytest-asyncio for async tests
- pytest-cov for coverage

**Monitoring**:
- Structured logging (JSON format)
- Error tracking (Sentry or similar)
- Performance monitoring
- Database query monitoring

### Security Considerations

**1. Agent Isolation**
- Each user's AI agent is completely isolated
- Agent ID validation on every access
- Conversation history encrypted at rest
- No cross-user data leakage

**2. Credit Management**
- Atomic credit transactions
- Audit trail for all credit operations
- Admin balance validation
- Rate limiting on credit operations

**3. API Security**
- Automaton API key stored in environment variables
- API timeout limits
- Retry limits to prevent abuse
- Request validation

**4. Data Privacy**
- User mode state encrypted
- Conversation history not shared
- Admin actions logged for audit
- GDPR-compliant data retention

### Performance Considerations

**1. Mode Transitions**
- Target: < 2 seconds
- Use async operations
- Minimize database queries
- Cache Genesis Prompt in memory

**2. Credit Operations**
- Use database transactions
- Batch credit updates where possible
- Index on user_id for fast lookups

**3. Agent Operations**
- Lazy load agents (create on first use)
- Cache active sessions in memory
- Clean up expired sessions periodically

**4. Database Optimization**
- Indexes on frequently queried columns
- Partition large tables by date
- Regular vacuum and analyze
- Connection pooling

### Monitoring and Observability

**Key Metrics**:
- Mode transition success rate
- Average transition time
- Credit transaction volume
- Active online sessions count
- AI agent response time
- Error rate by category
- Admin action frequency

**Alerts**:
- Mode transition failure rate > 5%
- Automaton API downtime
- Credit transaction failures
- Agent isolation violations
- Database connection issues

**Dashboards**:
- Real-time mode distribution (offline vs online)
- Credit usage trends
- Active sessions over time
- Error rate trends
- Performance metrics

### Migration Strategy

**Existing Users**:
- Default all existing users to offline mode
- Preserve existing credit balances
- Migrate existing AI agent data to isolated_ai_agents table
- No disruption to current functionality

**Rollout Plan**:
1. Deploy to staging environment
2. Test with internal users (1 week)
3. Beta release to 10% of users
4. Monitor metrics and gather feedback
5. Gradual rollout to 50%, then 100%
6. Post-deployment monitoring (2 weeks)

### Future Enhancements

**Potential Features**:
- Hybrid mode (offline + online features)
- Credit packages and subscriptions
- Agent performance analytics
- Multi-agent support per user
- Agent customization options
- Voice mode for AI agent
- Mobile app integration

## Summary

This design document outlines a comprehensive dual-mode system for the CryptoMentor Telegram bot that provides users with flexible trading options:

**Offline Mode**: Cost-effective manual trading with technical analysis and futures signals using Binance API without LLM processing.

**Online Mode**: Premium AI-powered trading with isolated personal agents, natural language interaction, and automated signal generation using Automaton API.

The architecture ensures:
- Clear separation of concerns between modes
- Robust credit management and validation
- Complete agent isolation for security
- Graceful error handling and fallback mechanisms
- Comprehensive testing with property-based tests
- Smooth user experience with clear UI/UX distinction

The implementation follows a phased approach with estimated 26-33 days of development effort, prioritizing core infrastructure and high-priority features first. The system is designed for scalability, security, and maintainability with comprehensive monitoring and observability.

