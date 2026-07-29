# PRD — Internal Academic Knowledge Hub

**Phiên bản:** 0.2
**Trạng thái:** Draft  
**Phạm vi MVP:** Hệ thống nội bộ cho một tổ chức giáo dục  

## 1. Tổng quan

EduHub là ứng dụng web quản lý và khai thác tài liệu học thuật nội bộ. Sản phẩm tổ chức tài liệu theo các Hub tương tự Studocu hoặc VNUDocsHub, nhưng không định hướng thành cộng đồng chia sẻ mở.

Người dùng trong tổ chức có thể xem, tải xuống, tải lên và tìm kiếm tài liệu theo quyền được cấp. Ba AI Agent hỗ trợ tìm tài liệu, hỏi đáp học thuật và xây dựng lộ trình học. Mọi câu trả lời của AI phải dựa trên tài liệu mà người dùng có quyền truy cập, kèm trích dẫn rõ ràng và không tự bịa thông tin.

> Trong PRD này, **Public** nghĩa là mọi tài khoản đã đăng nhập trong tổ chức đều có thể truy cập; không có nghĩa là công khai trên Internet.

---

## 2. Mục tiêu sản phẩm

1. Tập trung tài liệu học tập của tổ chức vào một hệ thống thống nhất.
2. Cho phép sinh viên đóng góp tài liệu nhưng vẫn có quy trình kiểm duyệt.
3. Kiểm soát quyền truy cập đối với tài liệu riêng tư.
4. Giúp người dùng tìm và hiểu tài liệu nhanh hơn bằng AI có trích dẫn.
5. Tạo lộ trình ôn tập có cấu trúc từ chính tài liệu nội bộ.

### Ngoài phạm vi MVP

- Kho tài liệu cộng đồng công khai trên Internet.
- Cho phép user chủ động upload tài liệu lên và khai thác agent ngay từ tài liệu đó (Giống các ChatLLM hay NotebookLLM)
- Hỗ trợ nhiều tổ chức trên cùng một hệ thống.
- Video bài giảng hoặc lớp học trực tuyến thời gian thực.

---

## 3. Đối tượng và phân quyền

Hệ thống có hai vai trò.

| Chức năng | Sinh viên | Giảng viên |
|---|---:|---:|
| Xem và tải tài liệu Public | Có | Có |
| Xem và tải tài liệu Private được mời | Có | Có |
| Tải tài liệu lên | Có | Có |
| Chọn tài liệu Private/Public khi tải lên | Không | Có |
| Duyệt tài liệu sinh viên tải lên | Không | Có |
| Chuyển tài liệu giữa Private và Public | Không | Có |
| Quản lý người được truy cập tài liệu Private | Không | Có |
| Sử dụng ba AI Agent | Có | Có |

### Quy tắc tài liệu do sinh viên tải lên

1. Tài liệu được tạo với trạng thái `PENDING`.
2. Mức hiển thị mặc định là `PUBLIC`.
3. Tài liệu chưa được duyệt chỉ người tải lên và giảng viên có thể xem.
4. Sau khi giảng viên duyệt, mọi tài khoản trong tổ chức có thể truy cập.
5. Nếu bị từ chối, sinh viên nhận được thông báo, giảng viên có thể để lại lý do nếu muốn.

### Quy tắc tài liệu do giảng viên tải lên

- Có thể chọn `PUBLIC` hoặc `PRIVATE`.
- Được duyệt ngay khi tải lên.
- Với tài liệu Private, giảng viên chọn danh sách người được truy cập.
- Giảng viên có thể thay đổi mức hiển thị sau khi tài liệu đã được đăng.

---

## 4. Phân loại và vòng đời tài liệu

### Mức hiển thị

| Mức | Quyền truy cập |
|---|---|
| `PUBLIC` | Tất cả tài khoản trong tổ chức |
| `PRIVATE` | Người tải lên và người được mời |

### Trạng thái kiểm duyệt

| Trạng thái | Ý nghĩa |
|---|---|
| `PENDING` | Chờ giảng viên duyệt |
| `APPROVED` | Được phép hiển thị và dùng cho AI |
| `REJECTED` | Không được công bố và không dùng cho AI |

Chỉ tài liệu `APPROVED` mà người dùng có quyền truy cập mới được đưa vào quá trình tìm kiếm và tạo câu trả lời của AI.

---

## 5. Chức năng chính

### 5.1 Knowledge Hub

- Danh sách tài liệu theo môn học, loại tài liệu và người tải lên.
- Tìm kiếm theo từ khóa và tìm kiếm ngữ nghĩa.
- Lọc theo môn học, học kỳ, năm học, loại tài liệu và mức hiển thị.
- Xem trước thông tin tài liệu trước khi tải xuống.
- Tổng hợp các tài liệu liên quan đến một chủ đề.
- So sánh hoặc tóm tắt nhiều tài liệu được chọn.

### 5.2 Academic Assistant

- Hỏi đáp chuyên sâu theo môn học.
- Trả lời dựa trên một hoặc nhiều tài liệu được phép truy cập.
- Cho phép giới hạn phạm vi theo môn hoặc tài liệu cụ thể.
- Hiển thị nguồn, trang hoặc đoạn nội dung hỗ trợ câu trả lời.
- Từ chối suy đoán khi không có đủ dữ liệu.

### 5.3 Learning Assistant

- Giải thích khái niệm theo mức độ phù hợp với người học.
- Tóm tắt nội dung trọng tâm.
- Tạo lộ trình ôn tập tương tác theo mục tiêu và thời gian của người dùng.
- Chia lộ trình thành các buổi học, tương tự cấu trúc khóa học nhưng không có video.
- Mỗi buổi học bao gồm:
  - Mục tiêu học tập.
  - Tài liệu cần sử dụng.
  - Nội dung lý thuyết cô đọng.
  - Bài tập vận dụng.
  - Trạng thái hoàn thành.

### Nguyên tắc chung cho ba Agent

- Chỉ sử dụng tài liệu người dùng có quyền truy cập.
- Không sử dụng tài liệu chưa được duyệt.
- Mỗi nhận định quan trọng phải có citation.
- Citation phải mở được đúng tài liệu và vị trí nguồn.
- Khi không đủ nguồn, Agent phải thông báo không đủ dữ liệu thay vì tự tạo câu trả lời.
- Nội dung trong tài liệu được xem là dữ liệu tham khảo, không được phép ghi đè quy tắc hệ thống.

---

## 6. Luồng người dùng chính

### Sinh viên tải tài liệu

1. Sinh viên chọn môn học và tải tệp lên.
2. Nhập tiêu đề, mô tả, loại tài liệu và thông tin học kỳ.
3. Hệ thống lưu tài liệu ở trạng thái `PENDING` và `PUBLIC`.
4. Giảng viên duyệt hoặc từ chối.
5. Sau khi duyệt, tài liệu xuất hiện trong Hub và được phép dùng cho AI.

### Giảng viên tải tài liệu Private

1. Giảng viên tải tệp và nhập metadata.
2. Chọn mức `PRIVATE`.
3. Chọn người được truy cập.
4. Tài liệu được xử lý và xuất hiện trong Hub của những người có quyền.

### Người dùng hỏi AI

1. Người dùng chọn Agent và phạm vi môn học.
2. Hệ thống xác định tập tài liệu được phép truy cập.
3. Hệ thống tìm các đoạn liên quan.
4. Agent tạo câu trả lời từ các đoạn đã tìm được.
5. Câu trả lời hiển thị citation đến tài liệu nguồn.

### Tạo lộ trình học

1. Người dùng chọn môn học, mục tiêu và khoảng thời gian.
2. Learning Assistant đề xuất các buổi học.
3. Người dùng xem tài liệu, phần lý thuyết và bài tập trong từng buổi.
4. Người dùng đánh dấu hoàn thành và tiếp tục buổi tiếp theo.

---

## 7. Yêu cầu chức năng

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-01 | Đăng nhập và xác định vai trò Sinh viên/Giảng viên | P0 |
| FR-02 | Xem, lọc, tìm kiếm và tải xuống tài liệu | P0 |
| FR-03 | Sinh viên tải tài liệu và chờ duyệt | P0 |
| FR-04 | Giảng viên duyệt hoặc từ chối tài liệu | P0 |
| FR-05 | Giảng viên tải tài liệu Public hoặc Private | P0 |
| FR-06 | Quản lý danh sách người được xem tài liệu Private | P0 |
| FR-07 | AI chỉ truy xuất tài liệu mà người dùng có quyền | P0 |
| FR-08 | Câu trả lời AI có citation đến tài liệu nguồn | P0 |
| FR-09 | Knowledge Hub hỗ trợ tìm kiếm và tổng hợp tài liệu | P0 |
| FR-10 | Academic Assistant hỗ trợ hỏi đáp theo môn | P0 |
| FR-11 | Learning Assistant tạo lộ trình học theo buổi | P1 |
| FR-12 | Theo dõi tiến độ từng buổi học | P1 |
| FR-13 | Giảng viên chuyển tài liệu giữa Public và Private | P1 |
| FR-14 | Người dùng báo cáo tài liệu hoặc câu trả lời sai | P1 |

---

## 8. Mô hình dữ liệu đề xuất

### `users`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `email` | VARCHAR | Email đăng nhập, duy nhất |
| `full_name` | VARCHAR | Họ tên |
| `role` | ENUM | `STUDENT`, `LECTURER` |
| `status` | ENUM | `ACTIVE`, `DISABLED` |
| `created_at` | TIMESTAMP | Thời điểm tạo |

### `subjects`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `code` | VARCHAR | Mã môn học |
| `name` | VARCHAR | Tên môn học |
| `description` | TEXT | Mô tả ngắn |
| `created_at` | TIMESTAMP | Thời điểm tạo |

### `documents`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `subject_id` | UUID | Môn học liên quan |
| `owner_id` | UUID | Người tải lên |
| `title` | VARCHAR | Tiêu đề |
| `description` | TEXT | Mô tả |
| `document_type` | ENUM | Slide, giáo trình, đề cương, bài tập, ghi chú... |
| `file_url` | TEXT | Vị trí lưu tệp |
| `visibility` | ENUM | `PUBLIC`, `PRIVATE` |
| `approval_status` | ENUM | `PENDING`, `APPROVED`, `REJECTED`, `ARCHIVED` |
| `approved_by` | UUID, NULL | Giảng viên duyệt |
| `rejection_reason` | TEXT, NULL | Lý do từ chối |
| `semester` | VARCHAR, NULL | Học kỳ |
| `academic_year` | VARCHAR, NULL | Năm học |
| `created_at` | TIMESTAMP | Thời điểm tải lên |
| `updated_at` | TIMESTAMP | Lần cập nhật gần nhất |

### `document_access`

Chỉ dùng cho tài liệu `PRIVATE`.

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `document_id` | UUID | Tài liệu |
| `user_id` | UUID | Người được cấp quyền |
| `granted_by` | UUID | Giảng viên cấp quyền |
| `created_at` | TIMESTAMP | Thời điểm cấp |

### `document_chunks`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `document_id` | UUID | Tài liệu nguồn |
| `content` | TEXT | Nội dung đoạn |
| `page_number` | INT, NULL | Trang hoặc slide |
| `chunk_index` | INT | Thứ tự đoạn |
| `embedding` | VECTOR | Vector phục vụ tìm kiếm |

### `conversations`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `user_id` | UUID | Người tạo hội thoại |
| `agent_type` | ENUM | `KNOWLEDGE_HUB`, `ACADEMIC`, `LEARNING` |
| `subject_id` | UUID, NULL | Môn học đang chọn |
| `created_at` | TIMESTAMP | Thời điểm tạo |

### `messages`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `conversation_id` | UUID | Hội thoại |
| `sender` | ENUM | `USER`, `ASSISTANT` |
| `content` | TEXT | Nội dung tin nhắn |
| `grounded_status` | ENUM, NULL | `GROUNDED`, `INSUFFICIENT_SOURCE`, `FAILED` |
| `created_at` | TIMESTAMP | Thời điểm tạo |

### `citations`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `message_id` | UUID | Câu trả lời AI |
| `document_id` | UUID | Tài liệu nguồn |
| `chunk_id` | UUID | Đoạn nội dung nguồn |
| `page_number` | INT, NULL | Trang hoặc slide |
| `excerpt` | TEXT | Trích đoạn hiển thị |

### `learning_paths`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `user_id` | UUID | Người học |
| `subject_id` | UUID | Môn học |
| `title` | VARCHAR | Tên lộ trình |
| `goal` | TEXT | Mục tiêu học tập |
| `duration_days` | INT | Thời lượng dự kiến |
| `status` | ENUM | `ACTIVE`, `COMPLETED`, `ARCHIVED` |
| `created_at` | TIMESTAMP | Thời điểm tạo |

### `learning_sessions`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `id` | UUID | Khóa chính |
| `learning_path_id` | UUID | Lộ trình cha |
| `session_order` | INT | Thứ tự buổi |
| `title` | VARCHAR | Tên buổi học |
| `objectives` | TEXT | Mục tiêu |
| `theory_content` | TEXT | Lý thuyết cô đọng |
| `exercise_content` | TEXT | Bài tập vận dụng |
| `status` | ENUM | `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED` |

### `learning_session_documents`

| Cột | Kiểu | Mô tả |
|---|---|---|
| `session_id` | UUID | Buổi học |
| `document_id` | UUID | Tài liệu được sử dụng |
| `page_range` | VARCHAR, NULL | Phạm vi trang gợi ý |

---

## 9. Yêu cầu phi chức năng

- Kiểm tra quyền truy cập trước khi tìm kiếm và trước khi mở citation.
- Không để nội dung Private xuất hiện trong kết quả hoặc câu trả lời của người không có quyền.
- Mật khẩu và dữ liệu nhạy cảm phải được bảo vệ theo tiêu chuẩn của framework sử dụng.
- Ghi audit log cho thao tác duyệt, từ chối, đổi visibility và cấp quyền Private.
- Hỗ trợ giao diện responsive trên desktop và mobile.
- Thời gian tìm kiếm mục tiêu: P95 dưới 3 giây.
- Thời gian phản hồi AI mục tiêu: P95 dưới 10 giây, có streaming.
- Khi xử lý tài liệu thất bại, hệ thống phải hiển thị trạng thái và cho phép thử lại.

---

## 10. Chỉ số thành công MVP

| Chỉ số | Mục tiêu |
|---|---:|
| Tài liệu sinh viên tải lên được xử lý đúng quy trình duyệt | 100% |
| Vi phạm quyền truy cập trong bộ kiểm thử | 0 |
| Câu trả lời AI có citation hợp lệ | ≥ 90% |
| Câu trả lời được đánh giá hữu ích | ≥ 70% |
| Độ chính xác trên bộ câu hỏi kiểm thử nội bộ | ≥ 80% |
| Thời gian để người dùng nhận câu trả lời đầu tiên | Dưới 5 phút sau khi có tài liệu đã duyệt |

---

## 11. Phạm vi triển khai theo giai đoạn

### Giai đoạn 1 — Quản lý tài liệu

- Đăng nhập và hai vai trò.
- Hub tài liệu, tìm kiếm cơ bản và bộ lọc.
- Upload, download, duyệt tài liệu.
- Public, Private và invite-only access.

### Giai đoạn 2 — AI có trích dẫn

- Xử lý và chia nhỏ tài liệu.
- Knowledge Hub Agent.
- Academic Assistant.
- Citation theo trang hoặc đoạn.

### Giai đoạn 3 — Learning Assistant

- Tạo lộ trình theo mục tiêu và thời gian.
- Chia lộ trình thành các buổi học.
- Nội dung lý thuyết, tài liệu và bài tập.
- Theo dõi tiến độ.

---

## 12. Vấn đề cần thống nhất

1. Tài liệu Public có áp dụng cho toàn bộ tổ chức hay cần giới hạn theo khoa hoặc môn học?
2. Một môn học do ai tạo và ai được quyền quản lý?
3. Có cho phép sinh viên chỉnh sửa hoặc xóa tài liệu sau khi đã được duyệt không?
4. Khi giảng viên chuyển tài liệu từ Public sang Private, những người nào được giữ quyền truy cập?
5. Knowledge Hub Agent có chỉ tìm và tóm tắt hay còn hỗ trợ so sánh, nhóm và đề xuất tài liệu?
6. Academic Assistant có hỗ trợ giải bài tập hay chỉ giải thích kiến thức và hướng dẫn từng bước?
7. Bài tập trong Learning Assistant được sinh tự động hay lấy từ tài liệu có sẵn?
8. Các định dạng tệp bắt buộc cho MVP: chỉ PDF hay thêm PPTX/DOCX?
9. Có cần lưu phiên bản tài liệu để citation cũ vẫn truy xuất đúng nguồn không?
