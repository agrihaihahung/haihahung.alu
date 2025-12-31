# import.py
# Import danh mục vật tư từ file data.json vào tonkho.db
# An toàn: trùng ma_hang sẽ skip

import json
from pathlib import Path
from sqlalchemy import create_engine, text

# ================= CONFIG =================
DB_PATH = "sqlite:///tonkho.db"
DATA_FILE = Path("data.json")   # file bạn đang có

# ================= MAIN =================
def main():
    print("📥 START IMPORT FROM data.json")

    if not DATA_FILE.exists():
        print(f"❌ Không tìm thấy file: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if "Data" not in raw or not isinstance(raw["Data"], list):
        print("❌ File JSON không đúng cấu trúc (thiếu key 'Data')")
        return

    rows = raw["Data"]

    engine = create_engine(DB_PATH, future=True)

    inserted = 0
    skipped = 0
    errors = 0

    with engine.begin() as conn:
        for idx, r in enumerate(rows, start=1):
            try:
                ma_hang = str(r.get("Mã Hàng hóa", "")).strip()
                if not ma_hang:
                    errors += 1
                    continue

                # check tồn tại
                exists = conn.execute(
                    text("SELECT 1 FROM materials WHERE ma_hang = :ma"),
                    {"ma": ma_hang}
                ).scalar()

                if exists:
                    skipped += 1
                    continue

                conn.execute(text("""
                    INSERT INTO materials (
                        he_nhom,
                        ma_hang,
                        ten_hang,
                        don_vi,
                        mau,
                        khoi_luong,
                        don_gia
                    ) VALUES (
                        :he_nhom,
                        :ma_hang,
                        :ten_hang,
                        :don_vi,
                        :mau,
                        :khoi_luong,
                        :don_gia
                    )
                """), {
                    "he_nhom": str(r.get("Hệ Nhôm", "")).strip(),
                    "ma_hang": ma_hang,
                    "ten_hang": str(r.get("Tên Hàng hóa", "")).strip(),
                    "don_vi": str(r.get("ĐVT", "")).strip(),
                    "mau": str(r.get("Màu", "")).strip(),
                    "khoi_luong": float(r.get("Khối lượng (kg/thanh)", 0) or 0),
                    "don_gia": float(r.get("Đơn giá", 0) or 0),
                })

                inserted += 1

            except Exception as e:
                print(f"⚠️ Lỗi dòng {idx}: {e}")
                errors += 1

    print("✅ IMPORT FINISHED")
    print(f"➕ Inserted : {inserted}")
    print(f"⏭️ Skipped  : {skipped} (trùng mã)")
    print(f"⚠️ Errors   : {errors}")


if __name__ == "__main__":
    main()
