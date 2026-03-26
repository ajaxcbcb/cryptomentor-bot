#!/usr/bin/env python3
"""
Cerebras AI Integration - Ultra Fast LLM
Uses Llama 3.1 70B via Cerebras Cloud
OpenAI-compatible API for easy integration
"""
import os
import logging
from openai import OpenAI
from typing import Optional

logger = logging.getLogger(__name__)

class CerebrasAI:
    """Cerebras AI client for ultra-fast LLM inference"""
    
    def __init__(self):
        """Initialize Cerebras client"""
        self.api_key = os.getenv('CEREBRAS_API_KEY')
        self.available = bool(self.api_key)
        
        if not self.available:
            logger.warning("⚠️ CEREBRAS_API_KEY not found - AI features disabled")
            self.client = None
            return
        
        try:
            # Initialize OpenAI-compatible client
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.cerebras.ai/v1"
            )
            logger.info("✅ Cerebras AI initialized (Llama 3.1 8B)")
        except Exception as e:
            logger.error(f"Failed to initialize Cerebras: {e}")
            self.available = False
            self.client = None
    
    async def analyze_market_simple(self, symbol: str, market_data: dict, language: str = 'id') -> str:
        """
        Analyze market with Cerebras AI - ULTRA FAST
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC')
            market_data: Market data dict with price, change, volume
            language: 'id' or 'en'
        
        Returns:
            Analysis text in markdown format
        """
        if not self.available:
            return "❌ AI not available (API key missing)"
        
        try:
            # Extract market data
            price = market_data.get('price', 0)
            change_24h = market_data.get('change_24h', 0)
            volume_24h = market_data.get('volume_24h', 0)
            
            # Build prompt
            if language == 'id':
                system_prompt = """Kamu adalah analis crypto expert. Berikan analisis singkat, padat, dan actionable.
Format:
1. Kondisi Market (2-3 kalimat)
2. Analisis Teknikal (2-3 kalimat)
3. Rekomendasi (1-2 kalimat)

Gunakan emoji untuk readability. Maksimal 150 kata."""
                
                user_prompt = f"""Analisis {symbol}:
• Harga: ${price:,.2f}
• Perubahan 24h: {change_24h:+.2f}%
• Volume 24h: ${volume_24h/1e9:.2f}B

Berikan analisis singkat untuk trader."""
            else:
                system_prompt = """You are an expert crypto analyst. Provide concise, actionable analysis.
Format:
1. Market Condition (2-3 sentences)
2. Technical Analysis (2-3 sentences)
3. Recommendation (1-2 sentences)

Use emojis for readability. Max 150 words."""
                
                user_prompt = f"""Analyze {symbol}:
• Price: ${price:,.2f}
• 24h Change: {change_24h:+.2f}%
• 24h Volume: ${volume_24h/1e9:.2f}B

Provide brief analysis for traders."""
            
            # Call Cerebras API
            response = self.client.chat.completions.create(
                model="llama3.1-8b",  # Cerebras Llama 3.1 8B (fast & free)
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content
            
            # Format output
            header = f"🤖 **AI Analysis: {symbol}**\n\n" if language == 'id' else f"🤖 **AI Analysis: {symbol}**\n\n"
            footer = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n⚡ Powered by Cerebras AI (Llama 3.1 8B)"
            
            return header + analysis + footer
            
        except Exception as e:
            logger.error(f"Cerebras API error: {e}")
            return f"❌ AI analysis failed: {str(e)[:50]}"
    
    async def chat_about_market(self, user_message: str, language: str = 'id') -> str:
        """
        Chat with AI about crypto market - ULTRA FAST
        
        Args:
            user_message: User's question
            language: 'id' or 'en'
        
        Returns:
            AI response in markdown format
        """
        if not self.available:
            return "❌ AI not available (API key missing)"
        
        try:
            # Build system prompt
            if language == 'id':
                system_prompt = """Kamu adalah CryptoMentor AI, asisten trading crypto yang helpful dan knowledgeable.

Karakteristik:
• Berikan jawaban yang jelas dan actionable
• Gunakan analogi sederhana untuk konsep kompleks
• Fokus pada edukasi dan risk management
• Jangan berikan financial advice (bukan rekomendasi beli/jual)
• Maksimal 200 kata per response

Gunakan emoji untuk readability."""
            else:
                system_prompt = """You are CryptoMentor AI, a helpful and knowledgeable crypto trading assistant.

Characteristics:
• Provide clear and actionable answers
• Use simple analogies for complex concepts
• Focus on education and risk management
• Don't give financial advice (no buy/sell recommendations)
• Max 200 words per response

Use emojis for readability."""
            
            # Call Cerebras API
            response = self.client.chat.completions.create(
                model="llama3.1-8b",  # Cerebras Llama 3.1 8B (fast & free)
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=400,
                temperature=0.8
            )
            
            answer = response.choices[0].message.content
            
            # Format output
            footer = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n⚡ Powered by Cerebras AI"
            
            return answer + footer
            
        except Exception as e:
            logger.error(f"Cerebras chat error: {e}")
            return f"❌ Chat failed: {str(e)[:50]}"
    
    def get_market_summary_prompt(self, market_data_list: list) -> str:
        """Generate market summary prompt from multiple coins data"""
        summary = "📊 Top 10 Crypto Market Data:\n\n"
        
        for data in market_data_list:
            symbol = data.get('symbol', 'N/A')
            price = data.get('price', 0)
            change = data.get('change_24h', 0)
            volume = data.get('volume_24h', 0)
            
            emoji = "🟢" if change > 0 else "🔴"
            summary += f"{emoji} {symbol}: ${price:,.2f} ({change:+.2f}%) | Vol: ${volume/1e9:.1f}B\n"
        
        return summary

# Global instance
cerebras_ai = CerebrasAI()
