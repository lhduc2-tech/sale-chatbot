import os
import psycopg2
from psycopg2.extras import RealDictCursor
from core.security_context import current_shop_id

def check_product_stock(product_name: str) -> str:
    """Tra cứu số lượng tồn kho của một sản phẩm bất kỳ trong cơ sở dữ liệu.
    
    Args:
        product_name: Tên của sản phẩm cần tra cứu (ví dụ: 'giày nike', 'iphone')
        
    Returns:
        Câu trả lời chứa tổng số lượng tồn kho thực tế của sản phẩm.
    """
    db_url = os.getenv("DB_URL")
    if not db_url:
        return "Lỗi: Hệ thống chưa cấu hình biến môi trường DB_URL trên server (Render/HF)."

    # Xóa dấu nháy kép hoặc đơn thừa nếu người dùng lỡ nhập dư trên Render Dashboard
    db_url = db_url.strip('"').strip("'")
    # Lấy shop_id từ biến ngữ cảnh (được truyền từ api.py hoặc app.py)
    shop_id = current_shop_id.get()

    conn = None
    try:
        # Cắm trực tiếp vào DB PostgreSQL bằng Psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=10)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Móc nối bảng products và inventories bằng Raw SQL
        query = """
            SELECT p.name, p.code, COALESCE(SUM(i.quantity), 0) AS total_qty
            FROM products p
            LEFT JOIN inventories i ON p.id = i.product_id
            WHERE p.name ILIKE %s
        """
        
        args = [f"%{product_name}%"]
        
        # Filter theo shop_id nếu user đang đăng nhập
        if shop_id:
            query += " AND p.shop_id = %s"
            args.append(shop_id)
            
        query += " GROUP BY p.name, p.code"
        
        cursor.execute(query, tuple(args))
        
        data = cursor.fetchall()
        
        if not data:
            shop_context = f" (thuộc quyền quản lý của cửa hàng {shop_id})" if shop_id else ""
            return f"Không tìm thấy sản phẩm nào chứa từ khóa '{product_name}' trong cơ sở dữ liệu{shop_context}."
            
        results = []
        for row in data:
            p_name = row.get("name", "Không rõ tên")
            p_code = row.get("code", "")
            total_qty = int(row.get("total_qty", 0))
            
            if total_qty > 0:
                results.append(f"Sản phẩm '{p_name}' (Mã: {p_code}) có tồn kho là {total_qty} cái.")
            else:
                results.append(f"Sản phẩm '{p_name}' (Mã: {p_code}) hiện tại đang hết hàng (tồn kho: 0).")
                
        return "\n".join(results)
        
    except psycopg2.Error as e:
        return f"Lỗi truy vấn SQL: {e.pgerror or str(e)}"
    except Exception as e:
        return f"Đã xảy ra lỗi kỹ thuật khi kết nối cơ sở dữ liệu: {str(e)}"
    finally:
        if conn:
            conn.close()
