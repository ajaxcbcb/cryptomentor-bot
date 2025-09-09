
# app/utils/text_formatter.py
import re
MD_SPECIAL = r"_[]()~`>#+-=|{}.!*"
def escape_md(text: str) -> str:
    return re.sub(rf"([\\{MD_SPECIAL}])", r"\\\1", text)
def bold(text: str) -> str:
    return f"*{escape_md(text)}*"
def code(text: str) -> str:
    return f"`{escape_md(text)}`"
