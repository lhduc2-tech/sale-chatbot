"""
Script tiện ích: Upload các file PDF từ thư mục `data/` local lên Supabase S3.

Sử dụng:
    python upload_pdfs.py                  # upload toàn bộ PDF trong data/
    python upload_pdfs.py file1.pdf        # upload một hoặc nhiều file cụ thể
"""

import os
import sys
import argparse
from dotenv import load_dotenv

from storage.supabase_s3 import upload_pdf, list_pdf_files


def main():
    load_dotenv()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(base_dir, "data")

    parser = argparse.ArgumentParser(
        description="Upload PDF lên Supabase S3 bucket"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Các file PDF cần upload (để trống để upload toàn bộ thư mục data/)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liệt kê các file PDF đang có trên S3",
    )
    args = parser.parse_args()

    if args.list:
        print("── Danh sách PDF trên Supabase S3 ──")
        keys = list_pdf_files()
        if not keys:
            print("  (Chưa có file nào)")
        for key in keys:
            print(f"  • {key}")
        return

    if args.files:
        # Upload các file được chỉ định
        for filename in args.files:
            local_path = filename if os.path.isabs(filename) else os.path.join(data_folder, filename)
            if not os.path.exists(local_path):
                print(f"[!] Không tìm thấy file: {local_path}")
                continue
            upload_pdf(local_path)
    else:
        # Upload toàn bộ PDF trong data/
        pdf_files = [f for f in os.listdir(data_folder) if f.lower().endswith(".pdf")]
        if not pdf_files:
            print(f"Không tìm thấy file PDF nào trong: {data_folder}")
            sys.exit(1)

        print(f"Tìm thấy {len(pdf_files)} file PDF. Bắt đầu upload...")
        for filename in pdf_files:
            local_path = os.path.join(data_folder, filename)
            upload_pdf(local_path)

    print("\n✅ Upload hoàn tất!")


if __name__ == "__main__":
    main()
