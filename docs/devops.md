# Hướng Dẫn DevOps & Đóng Gói Container (DevOps & CI/CD Spec)

> **Dự án:** OnBxrd (BDSO2O-10)
> **Giai đoạn:** Phase 4 (DevOps & Containerization — Tuần 5)

---

## 1. Cấu Hình Docker Container

Dự án được container hóa bằng `Dockerfile` (Backend FastAPI) và `docker-compose.yml` (Local Stack).

### 1.1 Khởi chạy môi trường local bằng Docker Compose
```bash
# Build và chạy container ở background
docker-compose up -d --build

# Kiểm tra status các container
docker-compose ps

# Xem log runtime của ứng dụng
docker-compose logs -f app
```

---

## 2. Quy Trình CI/CD (GitHub Actions Workflow)

File cấu hình CI nằm tại `.github/workflows/ci.yml`. Tự động kích hoạt khi có `push` hoặc `pull_request` vào nhánh `main` / `develop`.

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Code Quality & Linting
        run: |
          pip install ruff
          ruff check .
      - name: Run Pytest
        run: |
          pytest tests/ -v
```

---

## 3. Quản Lý Biến Môi Trường Trọng Yếu (Secrets Management)
- KHÔNG BAO GIỜ commit `.env` chứa API Keys thật lên GitHub.
- Trên GitHub Repository, vào `Settings` -> `Secrets and variables` -> `Actions` để thêm các secrets:
  - `OPENAI_API_KEY`
  - `LANGCHAIN_API_KEY`
  - `DATABASE_URL`
