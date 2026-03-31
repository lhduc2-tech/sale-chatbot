import contextvars
from typing import Optional
import json
import base64

# Biến ngữ cảnh toàn cục (thread-safe, async-safe) dùng để lưu shop_id
# của người dùng đang gửi request hiện tại.
current_shop_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_shop_id", default=None
)

def decode_jwt_shop_id(token: str) -> Optional[str]:
    """Hàm tự động giải mã JWT để lấy shopId mà không cần cài thêm thư viện."""
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        
        parts = token.split('.')
        if len(parts) != 3:
            return None
            
        payload_b64 = parts[1]
        # Bổ sung padding nếu Base64 bị khuyết
        padded_b64 = payload_b64 + '=' * (-len(payload_b64) % 4)
        
        decoded_bytes = base64.urlsafe_b64decode(padded_b64)
        payload_json = json.loads(decoded_bytes.decode('utf-8'))
        
        return payload_json.get('shopId')
    except Exception as e:
        print(f"Lỗi giải mã token: {e}")
        return None
