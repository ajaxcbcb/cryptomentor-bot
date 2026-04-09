"""
UI Components for Better User Experience
Reusable components for consistent UI/UX across the bot
"""

def progress_indicator(current_step: int, total_steps: int, step_name: str = "") -> str:
    """
    Generate visual progress indicator
    
    Args:
        current_step: Current step number (1-indexed)
        total_steps: Total number of steps
        step_name: Optional name of current step
    
    Returns:
        Formatted progress indicator string
    """
    filled = "▓" * current_step
    empty = "░" * (total_steps - current_step)
    percentage = int((current_step / total_steps) * 100)
    
    progress_bar = f"[{filled}{empty}] {percentage}%"
    step_info = f"Step {current_step}/{total_steps}"
    
    if step_name:
        step_info += f": {step_name}"
    
    return f"""━━━━━━━━━━━━━━━━━━━━
{progress_bar}
{step_info}
━━━━━━━━━━━━━━━━━━━━"""


def section_header(title: str, emoji: str = "📊") -> str:
    """Generate consistent section header"""
    return f"""
━━━━━━━━━━━━━━━━━━━━
{emoji} {title.upper()}
━━━━━━━━━━━━━━━━━━━━"""


def status_badge(is_active: bool) -> str:
    """Generate status badge"""
    return "🟢 Active" if is_active else "🔴 Inactive"


def format_currency(amount: float, currency: str = "USDT") -> str:
    """Format currency consistently"""
    return f"${amount:,.2f} {currency}"


def format_percentage(value: float, show_sign: bool = True) -> str:
    """Format percentage consistently"""
    sign = "+" if value > 0 and show_sign else ""
    return f"{sign}{value:.2f}%"


def quick_action_button(text: str, emoji: str = "▶️") -> str:
    """Format quick action button text"""
    return f"{emoji} {text}"


def error_message_actionable(
    title: str,
    steps: list,
    help_options: list = None
) -> str:
    """
    Format actionable error message
    
    Args:
        title: Error title (e.g., "❌ API Key Ditolak")
        steps: List of dicts with 'num', 'text', 'emoji' keys
        help_options: Optional list of help options
    
    Returns:
        Formatted error message with actionable steps
    """
    message = f"{title}\n\n🔧 <b>Fix in 2 minutes:</b>\n\n"

    for step in steps:
        num = step.get('num', '•')
        text = step.get('text', '')
        emoji = step.get('emoji', '')
        message += f"{num} {emoji} {text}\n"

    if help_options:
        message += "\n💬 <b>Need help?</b>\n"
        for option in help_options:
            message += f"   {option}\n"
    
    return message


def loading_message(action: str, tip: str = None) -> str:
    """
    Format loading message with optional tip
    
    Args:
        action: What's being loaded (e.g., "Verifying connection")
        tip: Optional tip to show while loading
    
    Returns:
        Formatted loading message
    """
    message = f"⏳ <b>{action}...</b>\n\n"
    
    if tip:
        message += f"💡 <b>Tip:</b> {tip}\n"
    
    return message


def success_message(title: str, details: dict = None) -> str:
    """
    Format success message
    
    Args:
        title: Success title
        details: Optional dict of details to show
    
    Returns:
        Formatted success message
    """
    message = f"✅ <b>{title}</b>\n\n"
    
    if details:
        for key, value in details.items():
            message += f"{key}: <b>{value}</b>\n"
    
    return message


def comparison_card(
    title: str,
    emoji: str,
    pros: list,
    cons: list = None,
    badge: str = None
) -> str:
    """
    Format comparison card for options
    
    Args:
        title: Card title
        emoji: Card emoji
        pros: List of pros
        cons: Optional list of cons
        badge: Optional badge (e.g., "RECOMMENDED")
    
    Returns:
        Formatted comparison card
    """
    header = f"{emoji} <b>{title}</b>"
    if badge:
        header += f" {badge}"
    
    message = f"""
━━━━━━━━━━━━━━━━━━━━
{header}
━━━━━━━━━━━━━━━━━━━━

"""
    
    for pro in pros:
        message += f"✅ {pro}\n"
    
    if cons:
        message += "\n"
        for con in cons:
            message += f"⚠️ {con}\n"
    
    return message


def settings_group(
    title: str,
    emoji: str,
    items: list,
    show_divider: bool = True
) -> str:
    """
    Format settings group
    
    Args:
        title: Group title
        emoji: Group emoji
        items: List of setting items (strings)
        show_divider: Whether to show divider
    
    Returns:
        Formatted settings group
    """
    message = ""
    
    if show_divider:
        message += section_header(title, emoji) + "\n\n"
    else:
        message += f"{emoji} <b>{title}</b>\n\n"
    
    for item in items:
        message += f"{item}\n"
    
    return message


def risk_level_indicator(leverage: int) -> tuple:
    """
    Get risk level indicator based on leverage
    
    Args:
        leverage: Leverage value
    
    Returns:
        Tuple of (emoji, label, description)
    """
    if leverage <= 10:
        return ("🟢", "LOW", "Suitable for beginners")
    elif leverage <= 25:
        return ("🟡", "MEDIUM", "Requires good risk management")
    elif leverage <= 50:
        return ("🟠", "HIGH", "For experienced traders only")
    else:
        return ("🔴", "VERY HIGH", "Extremely high liquidation risk")


def format_trade_summary(
    symbol: str,
    side: str,
    entry: float,
    sl: float,
    tp: float,
    leverage: int,
    margin: float
) -> str:
    """
    Format trade summary for confirmation
    
    Returns:
        Formatted trade summary
    """
    side_emoji = "🟢" if side == "LONG" else "🔴"
    risk_emoji, risk_label, risk_desc = risk_level_indicator(leverage)
    
    return f"""
{side_emoji} <b>{symbol} {side}</b>

📊 <b>Trade Details:</b>
• Entry: <code>{entry:.4f}</code>
• Stop Loss: <code>{sl:.4f}</code>
• Take Profit: <code>{tp:.4f}</code>

⚙️ <b>Position Settings:</b>
• Leverage: <b>{leverage}x</b>
• Margin: <b>{margin:.2f} USDT</b>
• Notional: <b>{margin * leverage:.2f} USDT</b>

{risk_emoji} <b>Risk Level: {risk_label}</b>
{risk_desc}
"""


def onboarding_welcome(total_steps: int = 4) -> str:
    """Generate welcoming onboarding message"""
    return f"""
🎉 <b>Welcome to CryptoMentor AutoTrade!</b>

<b>Setup in {total_steps} easy steps:</b>

1️⃣ Select Exchange
2️⃣ Connect API Key
3️⃣ Setup Risk Management
4️⃣ Start Trading

⏱ <b>Estimated time:</b> <b>5 minutes</b>

Let's get started! 🚀
"""


def help_menu() -> str:
    """Generate help menu"""
    return """
❓ <b>Need Help?</b>

📚 <b>Resources:</b>
• Tutorial Video
• FAQ
• User Guide

💬 <b>Support:</b>
• Chat Admin: @BillFarr
• Community Group
• Email Support

🔧 <b>Common Issues:</b>
• API Key Setup
• Balance Issues
• Trading Problems
"""


# Export all functions
__all__ = [
    'progress_indicator',
    'section_header',
    'status_badge',
    'format_currency',
    'format_percentage',
    'quick_action_button',
    'error_message_actionable',
    'loading_message',
    'success_message',
    'comparison_card',
    'settings_group',
    'risk_level_indicator',
    'format_trade_summary',
    'onboarding_welcome',
    'help_menu',
]
