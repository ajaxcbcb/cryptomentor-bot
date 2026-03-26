"""
Direct OpenAI API Provider
Faster and more reliable than OpenRouter
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not installed. Run: pip install openai")

class OpenAIDirectProvider:
    """Direct OpenAI API provider for faster, more reliable responses"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.available = bool(self.api_key) and OPENAI_AVAILABLE
        
        if self.available:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logging.info("✅ Direct OpenAI provider initialized")
        else:
            self.client = None
            if not self.api_key:
                logging.warning("⚠️ OPENAI_API_KEY not found in environment")
            if not OPENAI_AVAILABLE:
                logging.warning("⚠️ OpenAI library not installed")
    
    async def chat_completion(
        self,
        messages: list,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.5,
        max_tokens: int = 1000,
        timeout: int = 15
    ) -> Optional[str]:
        """
        Call OpenAI Chat Completion API directly
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}]
            model: Model name (gpt-3.5-turbo, gpt-4, etc)
            temperature: 0-2, lower = more focused
            max_tokens: Max response length
            timeout: Request timeout in seconds
        
        Returns:
            Response text or None if error
        """
        if not self.available:
            logging.error("OpenAI Direct provider not available")
            return None
        
        try:
            # Call OpenAI API with timeout
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ),
                timeout=timeout
            )
            
            # Extract response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                logging.info(f"✅ OpenAI response received ({len(content)} chars)")
                return content
            else:
                logging.error("OpenAI response has no choices")
                return None
        
        except asyncio.TimeoutError:
            logging.error(f"⚠️ OpenAI API timeout after {timeout}s")
            return None
        
        except Exception as e:
            logging.error(f"❌ OpenAI API error: {e}")
            return None
    
    async def analyze_market(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        language: str = 'id'
    ) -> str:
        """
        Analyze market using Direct OpenAI
        
        Args:
            symbol: Crypto symbol (BTC, ETH, etc)
            market_data: Market data dict
            language: Response language ('id' or 'en')
        
        Returns:
            Analysis text
        """
        if not self.available:
            return "❌ OpenAI Direct provider not available"
        
        try:
            # Extract market data
            price = market_data.get('price', 0)
            change_24h = market_data.get('change_24h', 0)
            volume_24h = market_data.get('volume_24h', 0)
            high_24h = market_data.get('high_24h', price)
            low_24h = market_data.get('low_24h', price)
            
            # Calculate metrics
            price_range = ((high_24h - low_24h) / low_24h * 100) if low_24h > 0 else 0
            
            # Determine condition
            if change_24h > 5:
                condition = "BULLISH KUAT 🚀"
            elif change_24h > 2:
                condition = "BULLISH 📈"
            elif change_24h > -2:
                condition = "SIDEWAYS ↔️"
            elif change_24h > -5:
                condition = "BEARISH 📉"
            else:
                condition = "BEARISH KUAT 🔻"
            
            # Create system prompt
            system_prompt = """Kamu adalah CryptoMentor AI, expert crypto analyst dengan pengalaman 10+ tahun.
Berikan analisis market yang mendalam, jelas, dan actionable.

Struktur analisis:
1. Kondisi market saat ini
2. Reasoning di balik pergerakan harga
3. Analisis volume dan volatilitas
4. Potensi pergerakan ke depan
5. Level support dan resistance
6. Risk dan opportunity
7. Rekomendasi dengan risk management

Gunakan bahasa yang santai tapi profesional. Selalu ingatkan tentang risk management."""

            if language == 'en':
                system_prompt = """You are CryptoMentor AI, an expert crypto analyst with 10+ years experience.
Provide in-depth, clear, and actionable market analysis.

Analysis structure:
1. Current market condition
2. Reasoning behind price movement
3. Volume and volatility analysis
4. Potential future movements
5. Support and resistance levels
6. Risks and opportunities
7. Recommendations with risk management

Use casual but professional language. Always remind about risk management."""
            
            # Create user prompt
            user_prompt = f"""Analisis Market untuk {symbol}:

📊 Data Real-time:
- Harga: ${price:,.2f}
- Perubahan 24j: {change_24h:+.2f}%
- Volume 24j: ${volume_24h:,.0f}
- High 24j: ${high_24h:,.2f}
- Low 24j: ${low_24h:,.2f}
- Range 24j: {price_range:.2f}%

📈 Kondisi: {condition}

Berikan analisis mendalam dengan reasoning yang jelas."""

            if language == 'en':
                user_prompt = f"""Market Analysis for {symbol}:

📊 Real-time Data:
- Price: ${price:,.2f}
- 24h Change: {change_24h:+.2f}%
- 24h Volume: ${volume_24h:,.0f}
- 24h High: ${high_24h:,.2f}
- 24h Low: ${low_24h:,.2f}
- 24h Range: {price_range:.2f}%

📈 Condition: {condition}

Provide in-depth analysis with clear reasoning."""
            
            # Call OpenAI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.5,
                max_tokens=1000,
                timeout=15
            )
            
            if response:
                # Format with header
                from datetime import datetime
                header = f"""🤖 **CRYPTOMENTOR AI ANALYSIS - {symbol}**
📊 **Market Data**: ${price:,.2f} ({change_24h:+.2f}%)
🕐 **Analysis Time**: {datetime.now().strftime('%H:%M:%S WIB')}
⚡ **Provider**: Direct OpenAI (Fast & Reliable)

---

"""
                return header + response
            else:
                return "❌ Failed to get response from OpenAI"
        
        except Exception as e:
            logging.error(f"Error in OpenAI market analysis: {e}")
            return f"❌ Error: {str(e)}"
    
    async def chat(
        self,
        user_message: str,
        language: str = 'id'
    ) -> str:
        """
        Chat with OpenAI
        
        Args:
            user_message: User's message
            language: Response language
        
        Returns:
            AI response
        """
        if not self.available:
            return "❌ OpenAI Direct provider not available"
        
        try:
            system_prompt = """Kamu adalah CryptoMentor AI, assistant yang friendly dan knowledgeable tentang cryptocurrency.
Kamu bisa diskusi santai tentang market, trading, dan crypto.

Karaktermu:
- Santai tapi informatif
- Bisa kasih insight valuable
- Tidak terlalu formal
- Bisa pakai emoji
- Jujur kalau tidak tahu
- Selalu ingatkan risk management"""

            if language == 'en':
                system_prompt = """You are CryptoMentor AI, a friendly and knowledgeable cryptocurrency assistant.
You can discuss markets, trading, and crypto casually.

Your characteristics:
- Casual but informative
- Provide valuable insights
- Not too formal
- Can use emojis
- Honest when unsure
- Always remind about risk management"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await self.chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=800,
                timeout=15
            )
            
            if response:
                return f"🤖 **CryptoMentor AI**:\n\n{response}"
            else:
                return "❌ Failed to get response from OpenAI"
        
        except Exception as e:
            logging.error(f"Error in OpenAI chat: {e}")
            return f"❌ Error: {str(e)}"

# Global instance
openai_direct = OpenAIDirectProvider()
