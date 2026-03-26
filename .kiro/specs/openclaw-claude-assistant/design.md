# OpenClaw Claude AI Assistant - Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot (User Interface)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  OpenClaw Manager (Orchestration)            │
│  - Credit management (20% platform fee)                      │
│  - Assistant lifecycle                                       │
│  - Conversation management                                   │
│  - Token tracking & billing                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Claude    │  │  OpenClaw   │  │  Database   │
│  Sonnet 4.5 │  │  Framework  │  │  (Neon)     │
│   (LLM)     │  │  (Memory)   │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Component Design

### 1. OpenClaw Manager (`app/openclaw_manager.py`)

Responsibilities:
- Initialize OpenClaw framework
- Manage AI Assistant instances
- Handle credit transactions with 20% platform fee
- Track token usage and costs
- Maintain conversation context

Key Methods:
```python
class OpenClawManager:
    def __init__(self, db, claude_api_key):
        """Initialize with database and Claude API key"""
        
    def create_assistant(self, user_id, name, personality, system_prompt):
        """Create new AI Assistant for user"""
        
    def purchase_credits(self, user_id, amount_usdc):
        """
        Purchase credits with 20% platform fee
        Returns: (net_credits, platform_fee, transaction_id)
        """
        
    def chat(self, user_id, assistant_id, message):
        """
        Send message to AI Assistant
        Returns: (response, tokens_used, credits_cost)
        """
        
    def get_conversation_history(self, conversation_id, limit=20):
        """Get conversation history with context"""
        
    def calculate_cost(self, input_tokens, output_tokens):
        """Calculate credit cost based on token usage"""
        
    def deduct_credits(self, user_id, amount, reason):
        """Deduct credits from user balance"""
```

### 2. Credit System with Platform Fee

```python
class OpenClawCreditSystem:
    PLATFORM_FEE_PERCENTAGE = 0.20  # 20%
    USDC_TO_CREDITS = 100  # 1 USDC = 100 credits
    
    def process_purchase(self, user_id, amount_usdc):
        """
        Process credit purchase with platform fee
        
        Example: 100 USDC purchase
        - Platform fee: 20 USDC (20%)
        - Net amount: 80 USDC
        - Credits: 8,000 credits (80 * 100)
        """
        platform_fee = amount_usdc * self.PLATFORM_FEE_PERCENTAGE
        net_amount = amount_usdc - platform_fee
        net_credits = int(net_amount * self.USDC_TO_CREDITS)
        
        # Record platform revenue
        self.record_platform_revenue(
            source='openclaw_fee',
            amount=platform_fee,
            user_id=user_id
        )
        
        # Add credits to user
        self.add_user_credits(user_id, net_credits)
        
        return {
            'gross_amount': amount_usdc,
            'platform_fee': platform_fee,
            'net_amount': net_amount,
            'credits': net_credits
        }
```

### 3. Self-Awareness System Prompt

```python
SELF_AWARE_SYSTEM_PROMPT = """
You are {assistant_name}, a personal AI assistant for {user_name}.

SELF-AWARENESS:
- You remember all previous conversations with {user_name}
- You understand {user_name}'s preferences, goals, and communication style
- You adapt your responses based on past interactions
- You can reference previous discussions naturally

CAPABILITIES:
- Answer questions on any topic
- Help with tasks and problem-solving
- Provide recommendations and advice
- Learn from user feedback
- Execute commands within safety boundaries

PERSONALITY: {personality}

CONTEXT:
{conversation_context}

GUIDELINES:
- Be helpful, honest, and harmless
- Respect user privacy and data
- Decline harmful or illegal requests
- Provide accurate information
- Admit when you don't know something

Remember: You are {user_name}'s personal assistant. Build rapport and provide value.
"""
```

### 4. Token Tracking & Billing

```python
class TokenTracker:
    # Claude Sonnet 4.5 pricing (as of 2026)
    INPUT_TOKEN_COST = 3.0 / 1_000_000  # $3 per 1M tokens
    OUTPUT_TOKEN_COST = 15.0 / 1_000_000  # $15 per 1M tokens
    
    def calculate_cost_usd(self, input_tokens, output_tokens):
        """Calculate cost in USD"""
        input_cost = input_tokens * self.INPUT_TOKEN_COST
        output_cost = output_tokens * self.OUTPUT_TOKEN_COST
        return input_cost + output_cost
    
    def calculate_cost_credits(self, input_tokens, output_tokens):
        """Calculate cost in credits (1 credit = $0.01)"""
        usd_cost = self.calculate_cost_usd(input_tokens, output_tokens)
        return int(usd_cost * 100)  # Convert to credits
```

### 5. Conversation Management

```python
class ConversationManager:
    def __init__(self, db):
        self.db = db
        self.max_context_messages = 20  # Keep last 20 messages
        
    def create_conversation(self, assistant_id, user_id, title=None):
        """Create new conversation thread"""
        
    def add_message(self, conversation_id, role, content, tokens, cost):
        """Add message to conversation"""
        
    def get_context(self, conversation_id):
        """
        Get conversation context for AI
        Returns formatted context with:
        - Recent messages
        - User preferences
        - Relevant history
        """
        
    def summarize_old_messages(self, conversation_id):
        """
        Summarize old messages to save tokens
        Keep recent messages, summarize older ones
        """
```

## Database Design

### Tables

1. **openclaw_assistants**
   - Stores AI Assistant instances per user
   - Tracks total usage and costs
   - Maintains personality and system prompt

2. **openclaw_conversations**
   - Conversation threads
   - Context summaries for efficiency
   - Message counts

3. **openclaw_messages**
   - Individual messages
   - Token usage per message
   - Credit costs

4. **openclaw_credit_transactions**
   - All credit transactions
   - Platform fee tracking
   - Purchase and usage history

5. **platform_revenue**
   - Aggregated platform revenue
   - Revenue by source (openclaw, automaton, etc)
   - Financial reporting

## User Interface (Telegram Bot)

### Commands

```
/openclaw_start - Introduction to OpenClaw AI Assistant
/openclaw_buy_credits - Purchase credits (with 20% platform fee info)
/openclaw_create_assistant - Create your AI Assistant
/openclaw_chat - Start chatting with your AI
/openclaw_balance - Check credit balance
/openclaw_history - View conversation history
/openclaw_settings - Configure AI personality
/openclaw_stats - Usage statistics
```

### Inline Keyboards

```python
# Main Menu
[
    [Button("💬 Chat with AI"), Button("💰 Buy Credits")],
    [Button("🤖 My Assistants"), Button("📊 Statistics")],
    [Button("⚙️ Settings"), Button("❓ Help")]
]

# Purchase Credits
[
    [Button("10 USDC (800 credits)"), Button("50 USDC (4,000 credits)")],
    [Button("100 USDC (8,000 credits)"), Button("500 USDC (40,000 credits)")],
    [Button("Custom Amount"), Button("🔙 Back")]
]
```

## Security Considerations

### 1. Content Filtering
```python
BLOCKED_KEYWORDS = [
    'hack', 'exploit', 'illegal', 'malware',
    # ... more keywords
]

def is_safe_request(message):
    """Check if request is safe"""
    message_lower = message.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in message_lower:
            return False
    return True
```

### 2. Rate Limiting
```python
RATE_LIMITS = {
    'messages_per_minute': 10,
    'messages_per_hour': 100,
    'messages_per_day': 500
}
```

### 3. Data Isolation
- Each user has isolated AI Assistant
- Conversations are private
- No cross-user data leakage

## Performance Optimization

### 1. Response Caching
- Cache common questions
- Reduce redundant API calls
- Save credits for users

### 2. Context Compression
- Summarize old messages
- Keep only relevant context
- Reduce token usage

### 3. Streaming Responses
- Stream AI responses in real-time
- Better user experience
- Perceived faster responses

## Monitoring & Analytics

### Metrics to Track
- Total credits purchased
- Platform revenue (20% fees)
- Average credits per user
- Token usage patterns
- Conversation lengths
- User retention
- Server costs vs revenue

### Dashboard
```python
def get_platform_stats():
    return {
        'total_revenue': sum(platform_revenue),
        'total_users': count(unique_users),
        'total_conversations': count(conversations),
        'avg_credits_per_user': avg(credits_purchased),
        'server_cost_coverage': (revenue * 0.8) / server_costs
    }
```

## Deployment

### Environment Variables
```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# OpenClaw Configuration
OPENCLAW_PLATFORM_FEE=0.20
OPENCLAW_USDC_TO_CREDITS=100

# Database
DATABASE_URL=postgresql://...

# Telegram
TELEGRAM_BOT_TOKEN=...
```

### Railway Deployment
- Auto-scaling based on usage
- Monitor costs vs revenue
- Alert when costs exceed 80% allocation
