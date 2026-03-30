import contextvars
from typing import Optional

# Biến ngữ cảnh toàn cục (thread-safe, async-safe) dùng để lưu shop_id
# của người dùng đang gửi request hiện tại.
current_shop_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_shop_id", default=None
)
