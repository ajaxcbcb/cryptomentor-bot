# Error Handler - Centralized Error Handling and Notification System
# Handles errors across all Automaton modules with admin notifications

import os
import traceback
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode
from datetime import datetime


class AutomatonErrorHandler:
    """
    Centralized error handling for Automaton system
    
    Features:
    - Error logging with context
    - Admin notifications for critical errors
    - Error categorization
    - Recovery suggestions
    """
    
    def __init__(self, bot: Optional[Bot] = None):
        """
        Initialize error handler
        
        Args:
            bot: Telegram Bot instance (optional, for admin notifications)
        """
        self.bot = bot
        self.admin_ids = self._load_admin_ids()
        print(f"✅ Automaton Error Handler initialized ({len(self.admin_ids)} admins)")
    
    def _load_admin_ids(self) -> list:
        """Load admin IDs from environment"""
        admin_ids = []
        
        for key in ['ADMIN_IDS', 'ADMIN1', 'ADMIN2', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
            value = os.getenv(key)
            if value:
                try:
                    if ',' in value:
                        admin_ids.extend([int(x.strip()) for x in value.split(',')])
                    else:
                        admin_ids.append(int(value))
                except ValueError:
                    pass
        
        return list(set(admin_ids))
    
    async def handle_wallet_generation_error(
        self,
        user_id: int,
        error: Exception,
        context: Optional[str] = None
    ):
        """
        Handle wallet generation errors
        
        Args:
            user_id: User ID
            error: Exception that occurred
            context: Optional context information
        """
        error_msg = f"Wallet generation error for user {user_id}: {str(error)}"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        # Log full traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Notify admins
        await self._notify_admins(
            title="🔴 Wallet Generation Error",
            message=f"User: {user_id}\nError: {str(error)}\nContext: {context or 'N/A'}",
            severity="critical"
        )
    
    async def handle_blockchain_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[str] = None
    ):
        """
        Handle blockchain interaction errors
        
        Args:
            operation: Operation that failed (e.g., "balance_check", "deposit_detection")
            error: Exception that occurred
            context: Optional context information
        """
        error_msg = f"Blockchain error during {operation}: {str(error)}"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        # Log full traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Notify admins for critical operations
        if operation in ['deposit_detection', 'withdrawal_processing']:
            await self._notify_admins(
                title="🔴 Blockchain Error",
                message=f"Operation: {operation}\nError: {str(error)}\nContext: {context or 'N/A'}",
                severity="critical"
            )
    
    async def handle_conway_api_error(
        self,
        endpoint: str,
        error: Exception,
        retry_count: int = 0,
        context: Optional[str] = None
    ):
        """
        Handle Conway API errors
        
        Args:
            endpoint: API endpoint that failed
            error: Exception that occurred
            retry_count: Number of retries attempted
            context: Optional context information
        """
        error_msg = f"Conway API error ({endpoint}): {str(error)} (retry {retry_count}/3)"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        # Notify admins after all retries exhausted
        if retry_count >= 3:
            await self._notify_admins(
                title="🔴 Conway API Error",
                message=f"Endpoint: {endpoint}\nError: {str(error)}\nRetries: {retry_count}\nContext: {context or 'N/A'}",
                severity="critical"
            )
    
    async def handle_database_error(
        self,
        operation: str,
        error: Exception,
        context: Optional[str] = None
    ):
        """
        Handle database errors
        
        Args:
            operation: Database operation that failed
            error: Exception that occurred
            context: Optional context information
        """
        error_msg = f"Database error during {operation}: {str(error)}"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        # Log full traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Notify admins
        await self._notify_admins(
            title="🔴 Database Error",
            message=f"Operation: {operation}\nError: {str(error)}\nContext: {context or 'N/A'}",
            severity="critical"
        )
    
    async def handle_deposit_processing_error(
        self,
        wallet_address: str,
        amount: float,
        error: Exception,
        context: Optional[str] = None
    ):
        """
        Handle deposit processing errors
        
        Args:
            wallet_address: Wallet address
            amount: Deposit amount
            error: Exception that occurred
            context: Optional context information
        """
        error_msg = f"Deposit processing error for {wallet_address} ({amount} USDC): {str(error)}"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        # Log full traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Notify admins
        await self._notify_admins(
            title="🔴 Deposit Processing Error",
            message=f"Wallet: {wallet_address}\nAmount: {amount} USDC\nError: {str(error)}\nContext: {context or 'N/A'}",
            severity="critical"
        )
    
    async def handle_spawn_error(
        self,
        user_id: int,
        agent_name: str,
        error: Exception,
        refund_needed: bool = False,
        context: Optional[str] = None
    ):
        """
        Handle agent spawn errors
        
        Args:
            user_id: User ID
            agent_name: Agent name
            error: Exception that occurred
            refund_needed: Whether spawn fee refund is needed
            context: Optional context information
        """
        error_msg = f"Spawn error for user {user_id} (agent: {agent_name}): {str(error)}"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        if refund_needed:
            print(f"   ⚠️ REFUND NEEDED: 100,000 credits for user {user_id}")
        
        # Log full traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Notify admins
        refund_text = "\n⚠️ REFUND NEEDED: 100,000 credits" if refund_needed else ""
        await self._notify_admins(
            title="🔴 Agent Spawn Error",
            message=f"User: {user_id}\nAgent: {agent_name}\nError: {str(error)}\nContext: {context or 'N/A'}{refund_text}",
            severity="critical"
        )
    
    async def handle_fee_collection_error(
        self,
        agent_id: str,
        fee_amount: float,
        error: Exception,
        context: Optional[str] = None
    ):
        """
        Handle performance fee collection errors
        
        Args:
            agent_id: Agent ID
            fee_amount: Fee amount
            error: Exception that occurred
            context: Optional context information
        """
        error_msg = f"Fee collection error for agent {agent_id} ({fee_amount} credits): {str(error)}"
        print(f"❌ {error_msg}")
        
        if context:
            print(f"   Context: {context}")
        
        # Log full traceback
        print(f"   Traceback: {traceback.format_exc()}")
        
        # Notify admins (warning level, not critical)
        await self._notify_admins(
            title="⚠️ Fee Collection Error",
            message=f"Agent: {agent_id}\nFee: {fee_amount} credits\nError: {str(error)}\nContext: {context or 'N/A'}",
            severity="warning"
        )
    
    async def _notify_admins(
        self,
        title: str,
        message: str,
        severity: str = "warning"
    ):
        """
        Send notification to all admins
        
        Args:
            title: Notification title
            message: Notification message
            severity: Severity level (critical/warning/info)
        """
        if not self.bot or not self.admin_ids:
            return
        
        # Format message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = (
            f"{title}\n\n"
            f"{message}\n\n"
            f"🕐 {timestamp}"
        )
        
        # Send to all admins
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=full_message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                print(f"❌ Failed to notify admin {admin_id}: {e}")


# Singleton instance
_error_handler = None

def get_error_handler(bot: Optional[Bot] = None) -> AutomatonErrorHandler:
    """
    Get singleton error handler instance
    
    Args:
        bot: Telegram Bot instance (optional)
        
    Returns:
        AutomatonErrorHandler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = AutomatonErrorHandler(bot)
    return _error_handler
