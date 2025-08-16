
import html
from typing import Iterable

MAX_LEN = 3500  # Safe below 4096 limit

def to_html(text: str) -> str:
    """Escape all HTML dangerous characters for safe Telegram parsing"""
    return html.escape(text, quote=False)

def chunk(text: str, max_len: int = MAX_LEN) -> Iterable[str]:
    """Split text into chunks that fit Telegram message limits"""
    if len(text) <= max_len:
        yield text
        return
    
    buf = []
    cur = 0
    for line in text.splitlines(True):  # keep newline
        if cur + len(line) > max_len and buf:
            yield "".join(buf)
            buf = [line]
            cur = len(line)
        else:
            buf.append(line)
            cur += len(line)
    
    if buf:
        yield "".join(buf)
