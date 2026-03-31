import re
from typing import List, Dict


class TextChunker:
    def __init__(self, chunk_size: int = 1500, overlap: int = 100):
        if overlap >= chunk_size:
            raise ValueError(f"overlap ({overlap}) phải nhỏ hơn chunk_size ({chunk_size})")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        chunks = []

        for doc in documents:
            content = doc.get("content", "")
            source = doc.get("source", "")
            
            # Phân tách văn bản dựa trên các Header Markdown (bắt đầu bằng "#")
            # prepend \n to correctly split the first line if it's a header
            sections = re.split(r'\n(?=#+\s)', "\n" + content)

            # Gom nhóm các section nhỏ liền nhau để tránh bị vỡ vụn ngữ cảnh 
            # (VD: # Tạo đơn hàng, # Bước 1, # Bước 2... cần được nằm chung 1 file nếu đủ chỗ)
            grouped_sections = []
            current_group = ""
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                # Kiểm tra section mới có phải là tiêu đề chính hay không (để tách chunk độc lập)
                header_match = re.search(r'^(#+)\s+(.*)', section)
                is_sub_section = False
                if header_match:
                    h_text = header_match.group(2).lower()
                    if h_text.startswith("bước") or h_text.startswith("step"):
                        is_sub_section = True
                        
                # Nếu cụm hiện tại đang chứa 1 topic, mà section mới cũng là 1 topic độc lập (VD: Xem cấu hình, Tạo mới)
                # thì ta buộc phải ngắt ra để truy xuất chính xác hơn, không nên nhồi chung dù còn chỗ.
                if current_group and header_match and not is_sub_section:
                    grouped_sections.append(current_group.strip())
                    current_group = section
                    continue
                    
                # Nối thêm vào cụm hiện tại nếu chưa vượt ngưỡng
                if len(current_group) + len(section) <= self.chunk_size:
                    current_group = current_group + "\n\n" + section if current_group else section
                else:
                    # Nếu vượt ngưỡng, chốt cụm đang nhồi dở
                    if current_group:
                        grouped_sections.append(current_group.strip())
                    
                    # Nếu chính section mới này to hơn chunk_size -> đẩy nó ra làm 1 cụm to
                    if len(section) > self.chunk_size:
                        grouped_sections.append(section)
                        current_group = ""
                    else:
                        current_group = section
                        
            # Lấy nốt cụm cuối cùng nếu còn
            if current_group:
                grouped_sections.append(current_group.strip())

            for group in grouped_sections:
                # Trích xuất Tiêu đề Header đầu tiên để làm bối cảnh (context) cho fallback
                header_match = re.search(r'^(#+\s+.*?)(?:\n|$)', group)
                header_context = ""
                if header_match:
                    header_context = header_match.group(1).strip()
                
                # Nếu cụm đủ nhỏ, cho vào làm 1 chunk luôn
                if len(group) <= self.chunk_size:
                    chunks.append({
                        "content": group,
                        "source": source
                    })
                else:
                    # Nếu lớn quá (1 section siêu dài) thì fallback lùi mốc cắt chữ
                    sub_chunks = self._word_based_chunk(group, source, header_context)
                    chunks.extend(sub_chunks)

        return chunks

    def _word_based_chunk(self, content: str, source: str, header_context: str) -> List[Dict]:
        """Chia chunk theo từ ngữ, được dùng như giải pháp dự phòng cho một phần quá dài"""
        chunks = []
        parts = re.split(r'(\s+)', content)
        
        start = 0
        is_first_chunk = True
        
        while start < len(parts):
            current_len = 0
            end = start
            
            # Sub-chunk thứ 2 trở đi sẽ được gắn nhẹ tên Tiêu đề ở đầu để AI nhớ nó đang đọc phần nào
            prefix = ""
            if not is_first_chunk and header_context:
                prefix = f"{header_context} (tiếp theo)...\n"
                
            allowance = self.chunk_size - len(prefix)
            if allowance < self.chunk_size // 2: 
                allowance = self.chunk_size
                prefix = ""
                
            while end < len(parts) and current_len + len(parts[end]) <= allowance:
                current_len += len(parts[end])
                end += 1
            
            if end == start:
                chunk_text = parts[end][:allowance]
                parts[start] = parts[end][allowance:]
            else:
                chunk_text = "".join(parts[start:end])
            
            if chunk_text.strip():
                final_content = prefix + chunk_text.strip()
                chunks.append({
                    "content": final_content,
                    "source": source
                })
                is_first_chunk = False

            if end == start:
                continue

            if end >= len(parts):
                break

            overlap_len = 0
            next_start = end
            
            for i in range(end - 1, start, -1):
                overlap_len += len(parts[i])
                if overlap_len >= self.overlap:
                    next_start = i
                    break
            
            start = max(next_start, start + 1)

        return chunks