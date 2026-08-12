# OnBxrd Frontend

Frontend độc lập cho OnBxrd, đặt trong `P-052/frontend`, tách khỏi backend và agent.

## Chạy local

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Mở `http://localhost:3000`. Mặc định app dùng dữ liệu mẫu để xem toàn bộ workspace. Khi backend chạy tại `http://localhost:8000`, đặt `NEXT_PUBLIC_USE_MOCKS=false` để dùng API thật; chỉ lỗi mất kết nối mới fallback sang dữ liệu mẫu, còn 401/403/404/409/422 được hiển thị đúng cho UI.

## Kiểm tra

```powershell
npm run typecheck
npm run build
npm run test
```

## Phạm vi MVP đã dựng

- Auth: login, register + OTP, forgot/reset password, đổi mật khẩu.
- Resident: home, chatbot, ticket form/list/detail/conversation, announcements, profile.
- Management: dashboard, ticket queue/detail, handoff, residents, accounts, announcements, knowledge, units.
- REST API client có bearer token, refresh một lần, mapping lỗi và fallback mock.
- SSE realtime connection indicator + query invalidation hook.
