import os
import boto3
from botocore.client import Config

# Prefix thư mục chứa PDF trên S3
S3_PDF_PREFIX = "data/"


def get_s3_client():
    """Khởi tạo S3 client kết nối tới Supabase S3-compatible storage."""
    endpoint  = os.getenv("S3_ENDPOINT")
    region    = os.getenv("S3_REGION")
    key_id    = os.getenv("S3_KEY_ID")
    access_key = os.getenv("S3_ACCESS_KEY")

    missing = [k for k, v in {
        "S3_ENDPOINT": endpoint,
        "S3_REGION":   region,
        "S3_KEY_ID":   key_id,
        "S3_ACCESS_KEY": access_key,
    }.items() if not v]

    if missing:
        raise EnvironmentError(
            f"[S3] Thiếu biến môi trường: {', '.join(missing)}. "
            "Vui lòng kiểm tra file .env"
        )

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=key_id,
        aws_secret_access_key=access_key,
        config=Config(signature_version="s3v4"),
    )


def upload_file(local_path: str, s3_key: str) -> None:
    """Upload một file từ local lên Supabase S3 bucket.

    Args:
        local_path: Đường dẫn file cục bộ cần upload.
        s3_key: Tên object key trên S3 (ví dụ: 'storage/faiss.index').
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    client = get_s3_client()
    client.upload_file(local_path, bucket, s3_key)
    print(f"[S3] Đã upload: {local_path} → s3://{bucket}/{s3_key}")


def download_file(s3_key: str, local_path: str) -> bool:
    """Download một file từ Supabase S3 về local.

    Args:
        s3_key: Tên object key trên S3.
        local_path: Đường dẫn lưu file cục bộ.

    Returns:
        True nếu download thành công, False nếu file không tồn tại trên S3.
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        print("[S3] ❌ Thiếu biến môi trường S3_BUCKET_NAME")
        return False

    try:
        client = get_s3_client()
    except EnvironmentError as e:
        print(f"[S3] ❌ {e}")
        return False

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        client.download_file(bucket, s3_key, local_path)
        print(f"[S3] ✅ Đã download: s3://{bucket}/{s3_key} → {local_path}")
        return True
    except client.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            print(f"[S3] ❌ Không tìm thấy file: s3://{bucket}/{s3_key}")
            return False
        print(f"[S3] ❌ Lỗi khi download '{s3_key}': [{error_code}] {e}")
        return False
    except Exception as e:
        print(f"[S3] ❌ Lỗi không xác định khi download '{s3_key}': {e}")
        return False


def list_pdf_files() -> list[str]:
    """Liệt kê tất cả file PDF trong thư mục 'data/' trên S3.

    Returns:
        Danh sách các object key của PDF (ví dụ: ['data/product.pdf', ...]).
        Trả về [] nếu có lỗi kết nối.
    """
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        print("[S3] ❌ Thiếu biến môi trường S3_BUCKET_NAME")
        return []

    try:
        client = get_s3_client()
    except EnvironmentError as e:
        print(f"[S3] ❌ {e}")
        return []

    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=S3_PDF_PREFIX)
        keys = [
            obj["Key"]
            for obj in response.get("Contents", [])
            if obj["Key"].lower().endswith(".pdf")
        ]
        if keys:
            print(f"[S3] ✅ Tìm thấy {len(keys)} file PDF trong s3://{bucket}/{S3_PDF_PREFIX}:")
            for k in keys:
                print(f"      • {k}")
        else:
            print(f"[S3] ⚠️  Không có file PDF nào trong s3://{bucket}/{S3_PDF_PREFIX}")
        return keys
    except Exception as e:
        print(f"[S3] ❌ Không thể liệt kê file từ bucket '{bucket}': {e}")
        return []


def upload_pdf(local_path: str) -> str:
    """Upload một file PDF lên thư mục 'data/' trên S3.

    Args:
        local_path: Đường dẫn PDF cục bộ.

    Returns:
        Object key trên S3.
    """
    filename = os.path.basename(local_path)
    s3_key = S3_PDF_PREFIX + filename
    upload_file(local_path, s3_key)
    return s3_key
