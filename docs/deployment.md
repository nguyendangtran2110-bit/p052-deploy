# Hướng Dẫn Deploy & Live Production URL (Deliverable #5)

> **Dự án:** OnBxrd (BDSO2O-10)
> **Giai đoạn:** Phase 4 (Triển khai Production — Tuần 5)
> **Trạng thái:** Live Production Ready

---

## 1. Thông Tin Production Endpoints (Live URLs)

| Thành phần | Môi trường Host | Live URL | Trạng thái |
| :--- | :--- | :--- | :---: |
| **Frontend Web App** | Vercel / Cloudflare | `https://onbxrd-app.vercel.app` | 🟢 Active |
| **Backend FastAPI** | Render / Railway | `https://onbxrd-api.onrender.com` | 🟢 Active |
| **API Docs (Swagger)**| Render / Railway | `https://onbxrd-api.onrender.com/docs` | 🟢 Active |
| **Vector DB / Storage**| Embedded ChromaDB | Internal Service Path | 🟢 Active |

---

## 2. Hướng Dẫn Deploy Chi Tiết

### 🚀 2.1 Deploy Backend lên Render.com
1. Đăng nhập [Render.com](https://render.com) -> Chọn **New Web Service**.
2. Kết nối với GitHub Repository `P-052`.
3. Cấu hình các thông số:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Khai báo các Environment Variables trong tab **Environment**:
   - `OPENAI_API_KEY`: `sk-proj-xxxxxxxx`
   - `ENVIRONMENT`: `production`

### 💻 2.2 Deploy Frontend lên Vercel
1. Đăng nhập [Vercel.com](https://vercel.com) -> Select Repository.
2. Cấu hình **Framework Preset:** `Next.js`.
3. Khai báo Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://onbxrd-api.onrender.com/api/v1`
4. Click **Deploy**.

---

## 3. Checklist Kiểm Tra Live URL Cho Demo Day
- [ ] Live URL truy cập ổn định từ mạng bên ngoài (không cần VPN/IP nội bộ).
- [ ] HTTPS Certificate hoạt động bình thường (không cảnh báo insecure SSL).
- [ ] Phản hồi câu hỏi RAG thành công với tốc độ < 3 giây.
- [ ] Giữ trạng thái Uptime cho đến hết Demo Day + 7 ngày.
