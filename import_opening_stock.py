# import_opening_stock.py
# Import tồn đầu kỳ vào bảng transactions

import json
from pathlib import Path
from sqlalchemy import create_engine, text

# ================= CONFIG =================
DB_PATH = "sqlite:///tonkho.db"
DATA_FILE = Path("ton_dau_ky.json")

# ================= MAIN =================
def main():
    print("📦 START IMPORT OPENING STOCK")

    if not DATA_FILE.exists():
        print(f"❌ Không tìm thấy file: {DATA_FILE}")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if "Data" not in raw:
        print("❌ JSON sai cấu trúc (thiếu key Data)")
        return

    engine = create_engine(DB_PATH, future=True)

    inserted = 0
    skipped = 0
    errors = 0

    with engine.begin() as conn:
        for i, r in enumerate(raw["Data"], start=1):
            try:
                ma = str(r.get("Mã Hàng hóa", "")).strip()
                qty = int(r.get("Số lượng", 0))

                if not ma or qty <= 0:
                    skipped += 1
                    continue

                material_id = conn.execute(
                    text("SELECT id FROM materials WHERE ma_hang = :ma"),
                    {"ma": ma}
                ).scalar()

                if not material_id:
                    print(f"⚠️ Không tìm thấy mã: {ma}")
                    errors += 1
                    continue

                conn.execute(text("""
                    INSERT INTO transactions (material_id, type, quantity)
                    VALUES (:id, 'IN', :qty)
                """), {
                    "id": material_id,
                    "qty": qty
                })

                inserted += 1

            except Exception as e:
                print(f"⚠️ Lỗi dòng {i}: {e}")
                errors += 1

    print("✅ IMPORT OPENING STOCK DONE")
    print(f"➕ Inserted : {inserted}")
    print(f"⏭️ Skipped  : {skipped}")
    print(f"⚠️ Errors   : {errors}")


if __name__ == "__main__":
    main()
