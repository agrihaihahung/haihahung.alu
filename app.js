const API = "http://127.0.0.1:8000";
let allMaterials = [];
let historyVisible = true;

// ================= LOAD HỆ NHÔM =================
async function loadHeNhom() {
  const res = await fetch(`${API}/materials`);
  allMaterials = await res.json();

  const heSelect = document.getElementById("heNhom");
  heSelect.innerHTML = "<option value=''>-- Chọn hệ nhôm --</option>";

  [...new Set(allMaterials.map(m => m.he_nhom))].forEach(h => {
    heSelect.innerHTML += `<option value="${h}">${h}</option>`;
  });
}

// ================= LOAD MÃ THEO HỆ =================
function loadMaterialsByHe() {
  const he = document.getElementById("heNhom").value;
  const select = document.getElementById("material");

  select.innerHTML = "<option value=''>-- Chọn mã nhôm --</option>";
  if (!he) return;

  allMaterials
    .filter(m => m.he_nhom === he)
    .forEach(m => {
      select.innerHTML += `<option value="${m.id}">${m.ma_hang}</option>`;
    });

  loadStock();
}

// ================= LOAD TỒN =================
async function loadStock() {
  const res = await fetch(`${API}/stock`);
  const data = await res.json();

  const tbody = document.getElementById("stock");
  tbody.innerHTML = "";

  data
    .filter(i => !heNhom.value || i.he_nhom === heNhom.value)
    .forEach(i => {
      tbody.innerHTML += `
        <tr>
          <td>${i.ma_hang}</td>
          <td>${i.stock}</td>
        </tr>
      `;
    });
}

// ================= LOAD LỊCH SỬ =================
async function loadHistory() {
  const res = await fetch(`${API}/history`);
  const data = await res.json();

  const tbody = document.getElementById("history");
  if (!tbody) return;

  tbody.innerHTML = "";

  data.forEach(i => {
    const typeText =
      i.type === "IN"
        ? "<span style='color:green;font-weight:bold'>NHẬP</span>"
        : "<span style='color:red;font-weight:bold'>XUẤT</span>";

    tbody.innerHTML += `
      <tr>
        <td>${i.created_at}</td>
        <td>${i.ma_hang}</td>
        <td>${typeText}</td>
        <td>${i.quantity}</td>
      </tr>
    `;
  });
}

// ================= NHẬP / XUẤT TAY =================
async function stockIn() {
  if (!material.value || qty.value <= 0) return alert("Nhập thiếu dữ liệu");

  await fetch(`${API}/in`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      material_id: Number(material.value),
      qty: Number(qty.value)
    })
  });

  qty.value = "";
  loadStock();
  loadHistory();
}

async function stockOut() {
  if (!material.value || qty.value <= 0) return alert("Nhập thiếu dữ liệu");

  await fetch(`${API}/out`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      material_id: Number(material.value),
      qty: Number(qty.value)
    })
  });

  qty.value = "";
  loadStock();
  loadHistory();
}

// ================= IMPORT EXCEL =================
async function importExcel() {
  const file = excelFile.files[0];
  if (!file) return alert("Chưa chọn file");

  const fd = new FormData();
  fd.append("file", file);

  const res = await fetch(`${API}/import-excel`, {
    method: "POST",
    body: fd
  });

  const data = await res.json();
  alert(`Nhập thành công ${data.inserted} dòng`);

  loadStock();
  loadHistory();
}

// ================= DOWNLOAD FILE =================
function downloadTemplate() {
  window.open(`${API}/download/template-import`, "_blank");
}

function downloadMaterials() {
  window.open(`${API}/download/materials`, "_blank");
}

// ================= TOGGLE HISTORY =================
function toggleHistory() {
  const table = document.getElementById("historyTable");
  const btn = document.getElementById("toggleHistoryBtn");

  historyVisible = !historyVisible;

  if (historyVisible) {
    table.style.display = "";
    btn.innerText = "Ẩn lịch sử";
  } else {
    table.style.display = "none";
    btn.innerText = "Hiện lịch sử";
  }
}

// ================= INIT =================
document.addEventListener("DOMContentLoaded", () => {
  loadHeNhom();
  heNhom.onchange = loadMaterialsByHe;
  loadStock();
  loadHistory();
});
// ================= FILTER TỒN KHO =================
function filterStock() {
  const keyword = document.getElementById("search").value.toLowerCase();
  const rows = document.querySelectorAll("#stock tr");

  rows.forEach(r => {
    const ma = r.children[0].innerText.toLowerCase();
    r.style.display = ma.includes(keyword) ? "" : "none";
  });
}

// ================= XUẤT EXCEL TỒN KHO =================
function downloadStock() {
  window.open(`${API}/download/stock`, "_blank");
}
