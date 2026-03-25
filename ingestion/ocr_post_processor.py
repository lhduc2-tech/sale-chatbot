"""
OCR Post-Processor: Tự động sửa lỗi OCR trong markdown bằng thư viện có sẵn.

Không dùng LLM — sử dụng:
  - ftfy       : sửa lỗi Unicode encoding (mojibake, ký tự sai)
  - underthesea: normalize text tiếng Việt
  - html + re  : clean HTML entities và ký tự rác
"""

import html
import re

try:
    import ftfy
    _HAS_FTFY = True
except ImportError:
    _HAS_FTFY = False
    print("[OCRPostProcessor] ftfy chưa được cài. Bỏ qua bước fix Unicode.")

try:
    from underthesea import text_normalize
    _HAS_UNDERTHESEA = True
except ImportError:
    _HAS_UNDERTHESEA = False
    print("[OCRPostProcessor] underthesea chưa được cài. Bỏ qua bước normalize tiếng Việt.")


# ── Regex patterns sửa lỗi OCR phổ biến ────────────────────────────────────
# Mỗi entry: (pattern, replacement)
_OCR_PATTERNS = [
    # Ký tự rác thường gặp trong OCR
    (r"[«»""''\u2018\u2019\u201c\u201d]", ""),         # smart quotes rác
    (r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", ""),         # control chars
    (r"[ \t]+$", ""),                                    # trailing whitespace mỗi dòng
    (r"\n{3,}", "\n\n"),                                 # nhiều dòng trống liên tiếp

    # OCR thường nhầm các cặp ký tự Latin phổ biến
    (r"\brn\b", "m"),                                    # 'rn' → 'm'
    (r"\bvv\b", "w"),                                    # 'vv' → 'w'

    # Markdown: heading bị lẫn vào text (# ở giữa câu)
    (r"(?<!\n)# ([A-ZĐÀÁẢÃẠĂẮẶẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ])", r"\1"),

    # Dấu gạch ngang / bullet lỗi
    (r"^[•·▪▸‣➔→\-–—]\s*", "- ", ),                    # chuẩn hóa bullet
]

# Compile để tái sử dụng
_COMPILED_PATTERNS = [
    (re.compile(pat, re.MULTILINE), repl)
    for pat, repl in _OCR_PATTERNS
]


class OCRPostProcessor:
    """
    Sửa lỗi OCR tự động, không cần LLM.

    Thứ tự xử lý:
      1. html.unescape()  — &amp; → &, &#124; → |, v.v.
      2. ftfy.fix_text()  — sửa Unicode encoding sai (nếu có cài ftfy)
      3. underthesea      — normalize text tiếng Việt (nếu có cài underthesea)
      4. Regex rules      — ký tự rác, bullet lỗi, dòng thừa, v.v.
    """

    def process(self, markdown: str) -> str:
        """Áp dụng toàn bộ pipeline sửa lỗi OCR."""
        # Bước 1: HTML entities
        markdown = html.unescape(markdown)

        # Bước 2: Fix Unicode encoding
        if _HAS_FTFY:
            markdown = ftfy.fix_text(markdown)

        # Bước 3: Normalize tiếng Việt (từng dòng để giữ cấu trúc markdown)
        if _HAS_UNDERTHESEA:
            lines = markdown.splitlines()
            markdown = "\n".join(
                text_normalize(line) if line.strip() else line
                for line in lines
            )

        # Bước 4: Regex rules
        for pattern, replacement in _COMPILED_PATTERNS:
            markdown = pattern.sub(replacement, markdown)

        return markdown.strip()
