# OpenClaw Claude AI Assistant - Requirements

## Overview
Sistem AI Assistant personal menggunakan OpenClaw + Claude Sonnet 4.5 dengan self-awareness, dimana user membeli credits dan platform mengambil 20% platform fee untuk profit dan sustainability.

## Business Model
- User membeli credits untuk menggunakan AI Assistant personal
- Platform fee: 20% dari total credits yang dibeli
- 80% sisanya untuk LLM usage dan operasional server Railway
- Self-sustaining system untuk biaya infrastructure

## Core Requirements

### 1. OpenClaw Integration
- Integrasi dengan OpenClaw framework untuk AI orchestration
- Claude Sonnet 4.5 sebagai LLM engine
- Self-awareness: AI dapat memahami konteks, history, dan tujuan user
- Persistent memory untuk setiap user

### 2. Credit System dengan Platform Fee
- User membeli credits (1 USDC = 100 credits)
- Platform fee: 20% dipotong saat pembelian
- 80% masuk ke user balance untuk LLM usage
- Contoh: Beli 100 USDC → Platform fee 20 USDC → User dapat 80 USDC (8,000 credits)

### 3. AI Assistant Features
- Personal AI Assistant untuk setiap user
- Dapat menjalankan semua perintah user (dalam batasan keamanan)
- Context-aware conversations
- Multi-turn dialogue dengan memory
- Task execution dan automation
- Learning dari interaksi user

### 4. Credit Usage Tracking
- Setiap request ke Claude API konsumsi credits
- Tracking per-token usage
- Real-time balance updates
- Notifikasi saat credits hampir habis

### 5. Self-Awareness Capabilities
- AI memahami siapa user-nya
- Mengingat preferensi dan history user
- Adaptive responses berdasarkan user behavior
- Personalized recommendations

### 6. Security & Safety
- Rate limiting untuk prevent abuse
- Content filtering untuk harmful requests
- Audit logging semua interactions
- User data isolation

## Technical Requirements

### Database Schema
```sql
-- OpenClaw AI Assistants
CREATE TABLE openclaw_assistants (
    assistant_id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name TEXT NOT NULL,
    personality TEXT,
    system_prompt TEXT,
    memory_context TEXT,
    total_tokens_used BIGINT DEFAULT 0,
    total_credits_spent DECIMAL(20,8) DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP
);

-- OpenClaw Conversations
CREATE TABLE openclaw_conversations (
    conversation_id TEXT PRIMARY KEY,
    assistant_id TEXT REFERENCES openclaw_assistants(assistant_id),
    user_id INTEGER REFERENCES users(id),
    title TEXT,
    context_summary TEXT,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OpenClaw Messages
CREATE TABLE openclaw_messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES openclaw_conversations(conversation_id),
    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tokens_used INTEGER,
    credits_cost DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OpenClaw Credit Transactions (with platform fee)
CREATE TABLE openclaw_credit_transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount_usdc DECIMAL(20,8) NOT NULL,
    platform_fee DECIMAL(20,8) NOT NULL, -- 20%
    net_credits INTEGER NOT NULL, -- 80% converted to credits
    transaction_type TEXT NOT NULL, -- 'purchase', 'usage', 'refund'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platform Revenue Tracking
CREATE TABLE platform_revenue (
    revenue_id TEXT PRIMARY KEY,
    source TEXT NOT NULL, -- 'openclaw_fee', 'automaton_fee', etc
    amount_usdc DECIMAL(20,8) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    transaction_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Integration
- OpenClaw SDK untuk AI orchestration
- Claude API (Anthropic) untuk LLM
- Token counting untuk accurate billing
- Streaming responses untuk better UX

### Credit Calculation
```
Purchase: 100 USDC
Platform Fee (20%): 20 USDC → Platform Revenue
Net Amount (80%): 80 USDC = 8,000 credits

Usage:
- Claude Sonnet 4.5: ~$3 per 1M input tokens, ~$15 per 1M output tokens
- Average conversation: ~1,000 tokens = ~$0.02
- 1 credit = $0.01 → 2 credits per conversation
- 8,000 credits = ~4,000 conversations
```

## User Flow

### 1. Purchase Credits
```
User → /openclaw_buy_credits
Bot → "Berapa USDC yang ingin Anda beli?"
User → "100 USDC"
Bot → "
💰 Purchase Summary:
Amount: 100 USDC
Platform Fee (20%): 20 USDC
Net Credits: 8,000 credits

Deposit ke: [wallet_address]
"
User → Deposit USDC
Bot → "✅ Credits received! Balance: 8,000 credits"
```

### 2. Create AI Assistant
```
User → /openclaw_create_assistant
Bot → "Beri nama AI Assistant Anda:"
User → "Alex"
Bot → "Pilih personality: [Friendly/Professional/Creative/Custom]"
User → "Friendly"
Bot → "✅ AI Assistant 'Alex' created! Start chatting with /openclaw_chat"
```

### 3. Chat with AI
```
User → /openclaw_chat
Bot → "💬 Chat with Alex (Balance: 8,000 credits)"
User → "Explain quantum computing"
AI → [Detailed explanation]
Bot → "Used 15 credits. Balance: 7,985 credits"
```

## Success Metrics
- User adoption rate
- Average credits purchased per user
- Platform revenue from 20% fee
- AI Assistant usage frequency
- User satisfaction scores
- Server cost coverage from 80% allocation

## Risks & Mitigations
- Risk: High LLM costs → Mitigation: Efficient token usage, caching
- Risk: User abuse → Mitigation: Rate limiting, content filtering
- Risk: Low adoption → Mitigation: Free trial credits, referral program
- Risk: Server costs exceed 80% → Mitigation: Dynamic pricing, optimization
