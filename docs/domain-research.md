# Báo Cáo Nghiên Cứu Thị Trường & Domain (Domain & Market Research)

> **Dự án:** OnBxrd (BDSO2O-10) — AI Resident Onboarding & Customer Care Assistant
> **Giai đoạn:** Phase 1 (Khởi tạo & Nghiên cứu — Tuần 1)
> **Trạng thái:** Template / In-Progress

---

## 1. Tổng Quan Thị Trường (Market Landscape)
- **Quy mô thị trường (TAM/SAM/SOM):**
  - **TAM (Total Addressable Market):** Thị trường quản lý bất động sản chung cư & khu đô thị tại Việt Nam / Đông Nam Á.
  - **SAM (Serviceable Addressable Market):** Các chủ đầu tư và đơn vị quản lý vận hành chung cư phân khúc trung & cao cấp.
  - **SOM (Serviceable Obtainable Market):** Các dự án bất động sản bàn giao mới trong vòng 1-2 năm tới.
- **Xu hướng ngành (Industry Trends):** Chuyển đổi số trong PropTech, tự động hóa quy trình cư dân move-in, áp dụng AI Agent giải đáp 24/7.

## 2. Phân Tích Bài Toán & Nhu Cầu Cư Dân (Problem & Pain Points)
| Đối tượng | Khó khăn hiện tại (Pain Points) | Tác động (Impact) |
| :--- | :--- | :--- |
| **Cư dân mới (Move-in Resident)** | Quy trình làm thủ tục phức tạp, thông tin phân tán trong sổ tay giấy, thời gian chờ phản hồi lâu. | Bức xúc, trải nghiệm bàn giao kém. |
| **Ban Quản Lý (Property Management)** | Quá tải phản hồi các câu hỏi lặp đi lặp lại (nội quy, phí dịch vụ, đăng ký thẻ xe), xử lý ticket sự cố thủ công. | Chi phí vận hành cao, phản hồi chậm. |
| **Chủ đầu tư (Developer)** | Thiếu dữ liệu đánh giá mức độ hài lòng của cư dân sau bàn giao. | Ảnh hưởng uy tín thương hiệu. |

## 3. Phân Tích Đối Thủ Cạnh Tranh (Competitive Benchmark)
| Tiêu chí | Giải pháp truyền thống (Sổ tay/Group Zalo) | Phần mềm BQL thông thường (App BQL) | **OnBxrd (AI Agent)** |
| :--- | :--- | :--- | :--- |
| **Hỗ trợ 24/7** | ❌ Không (chỉ giờ hành chính) | ⚠️ Có form gửi nhưng phản hồi chậm | ✅ AI phản hồi tức thì 24/7 |
| **Trả lời câu hỏi chính xác** | ❌ Cư dân tự tìm trong sổ tay | ❌ Tra cứu thủ công | ✅ RAG tìm kiếm chính xác kèm trích dẫn |
| **Quy trình Onboarding** | ❌ Thủ tục giấy tờ thủ công | ⚠️ Có danh sách nhưng thụ động | ✅ Interactive Checklist thông minh |
| **Xử lý ticket sự cố** | ❌ Phản ánh qua điện thoại/giấy | ⚠️ Phân loại thủ công | ✅ AI phân loại tự động & Human-in-the-Loop |

## 4. Đánh Giá Tính Khả Thi Kỹ Thuật & Chi Phí (Technical & Cost Feasibility)
- **RAG Capability:** Sử dụng LlamaIndex + ChromaDB để index sổ tay cư dân (PDF/Word), đảm bảo trích dẫn chính xác 100%.
- **LLM Engine & Cost:** Dùng `gpt-4o-mini` cho giai đoạn phát triển (~$5-$10 tổng chi phí testing), đảm bảo tốc độ phản hồi < 3s.
- **Rủi ro chính:** AI trả lời sai nội quy tòa nhà (Hallucination).
- **Giải pháp:** Bắt buộc có nguồn trích dẫn (citations) + cơ chế Human-in-the-Loop cho ticket phức tạp.
