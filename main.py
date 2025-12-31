from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import create_engine, text
from pydantic import BaseModel
import pandas as pd
import io

app = FastAPI(title="Quản lý tồn kho nhôm")

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DATABASE =================
engine = create_engine("sqlite:///tonkho.db", future=True, echo=False)

# ================= MODEL =================
class StockPayload(BaseModel):
    material_id: int
    qty: int

# ================= STARTUP =================
@app.on_event("startup")
def startup():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            he_nhom TEXT,
            ma_hang TEXT UNIQUE,
            ten_hang TEXT,
            don_vi TEXT,
            mau TEXT,
            khoi_luong REAL,
            don_gia REAL
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            type TEXT CHECK(type IN ('IN','OUT')),
            quantity INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """))

# ================= MATERIALS =================
@app.get("/materials")
def get_materials():
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT * FROM materials ORDER BY he_nhom, ma_hang")
        ).mappings().all()

# ================= IN / OUT =================
@app.post("/in")
def stock_in(p: StockPayload):
    with engine.begin() as conn:
        conn.execute(text("""
        INSERT INTO transactions (material_id, type, quantity)
        VALUES (:id, 'IN', :qty)
        """), {"id": p.material_id, "qty": p.qty})
    return {"status": "ok"}

@app.post("/out")
def stock_out(p: StockPayload):
    with engine.begin() as conn:
        conn.execute(text("""
        INSERT INTO transactions (material_id, type, quantity)
        VALUES (:id, 'OUT', :qty)
        """), {"id": p.material_id, "qty": p.qty})
    return {"status": "ok"}

# ================= STOCK =================
@app.get("/stock")
def get_stock():
    with engine.connect() as conn:
        return conn.execute(text("""
        SELECT
            m.he_nhom,
            m.ma_hang,
            COALESCE(SUM(
                CASE
                    WHEN t.type='IN' THEN t.quantity
                    WHEN t.type='OUT' THEN -t.quantity
                END
            ),0) AS stock
        FROM materials m
        LEFT JOIN transactions t ON m.id = t.material_id
        GROUP BY m.id
        HAVING stock != 0
        ORDER BY m.he_nhom, m.ma_hang
        """)).mappings().all()

# ================= HISTORY =================
@app.get("/history")
def history(limit: int = 100):
    with engine.connect() as conn:
        return conn.execute(text("""
        SELECT
            t.created_at,
            m.ma_hang,
            t.type,
            t.quantity
        FROM transactions t
        JOIN materials m ON m.id = t.material_id
        ORDER BY t.created_at DESC
        LIMIT :limit
        """), {"limit": limit}).mappings().all()

# ================= IMPORT EXCEL =================
@app.post("/import-excel")
async def import_excel(file: UploadFile = File(...)):
    df = pd.read_excel(file.file)

    success, errors = [], []

    with engine.begin() as conn:
        for idx, r in df.iterrows():
            ma = str(r["ma_hang"]).strip()
            qty = int(r["so_luong"])

            mid = conn.execute(
                text("SELECT id FROM materials WHERE ma_hang=:ma"),
                {"ma": ma}
            ).scalar()

            if not mid:
                errors.append({"row": idx+2, "ma_hang": ma, "error": "Không tồn tại"})
                continue

            conn.execute(text("""
            INSERT INTO transactions (material_id, type, quantity)
            VALUES (:id,'IN',:qty)
            """), {"id": mid, "qty": qty})

            success.append(ma)

    return {"inserted": len(success), "errors": errors}

# ================= DOWNLOAD TEMPLATE =================
@app.get("/download/template-import")
def download_template():
    df = pd.DataFrame({
        "ma_hang": ["N-K55-3318", "G-K55-3313"],
        "so_luong": [10, 5]
    })

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="NhapKho")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Template_NhapKho.xlsx"}
    )

# ================= DOWNLOAD MATERIALS =================
@app.get("/download/materials")
def download_materials():
    with engine.connect() as conn:
        df = pd.DataFrame(conn.execute(text("""
        SELECT he_nhom, ma_hang, ten_hang, mau, don_vi
        FROM materials
        ORDER BY he_nhom, ma_hang
        """)).mappings().all())

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="DanhMucMaNhom")
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=DanhMuc_MaNhom.xlsx"}
    )
