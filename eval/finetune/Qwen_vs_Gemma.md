# Báo cáo so sánh Qwen3-4B QLoRA và Gemma 4 E4B QLoRA

## Phạm vi và cách đọc kết quả

- Cả hai log được báo cáo trên **100 case** (`examples: 100`). Đây là smoke subset của held-out `test`, chưa phải toàn bộ 600 case. Cần chạy lại với `MAX_EVAL_CASES=None` trước khi chốt kết quả chính thức.
- `schema_valid_rate`, `intent_accuracy`, `action_accuracy` và `all_checks_pass_rate` là tỷ lệ. `required_field_completion` chỉ tính trên các case có trường bắt buộc áp dụng.
- Delta bên dưới là **Qwen trừ Gemma**: các metric tỷ lệ dùng điểm phần trăm; `average_quality_score` dùng điểm trên thang 0–100.

## Kết quả tổng quan

| Metric | Qwen3-4B finetuned | Gemma 4 E4B finetuned | Delta Qwen − Gemma | Nhận định |
|---|---:|---:|---:|---|
| Schema valid rate | 100.00% | 93.00% | +7.00 điểm % | Qwen luôn trả về JSON đúng schema; Gemma còn lỗi schema. |
| Intent accuracy | 99.00% | 66.00% | +33.00 điểm % | Gemma sai taxonomy/ý định ở nhiều flow. |
| Action accuracy | 92.00% | 56.00% | +36.00 điểm % | Đây là khoảng cách lớn nhất về hành vi có side effect. |
| Required-field completion | 100.00% | 54.29% | +45.71 điểm % | Gemma thường không chặn hoặc điền thiếu trường bắt buộc. |
| Average quality score | 97.67 | 80.34 | +17.33 điểm | Qwen ổn định hơn trên từng check thành phần. |
| All checks pass rate | 89.00% | 50.00% | +39.00 điểm % | Qwen có 11 case fail; Gemma có 50 case fail trên 100 case. |

### Kết luận lựa chọn model

Qwen3-4B QLoRA thắng Gemma 4 E4B QLoRA trên mọi metric đã đo và nên là lựa chọn hiện tại cho pipeline agent. Chênh lệch quan trọng nhất không phải chỉ là chất lượng ngôn ngữ, mà là tuân thủ contract: JSON/schema, intent/action canonical, điều kiện trường bắt buộc và flow xác nhận.

So sánh này phản ánh toàn bộ hệ thống fine-tune + prompt + cấu hình train hiện tại, không phải kết luận thuần túy về kiến trúc nền. Gemma phải train với giới hạn VRAM nghiêm ngặt hơn (single T4, context ngắn hơn), nên cần giữ điều kiện train/eval được ghi lại khi báo cáo cuối cùng.

## Phân tích lỗi Qwen3-4B

Qwen fail 11/100 case. Các lỗi tập trung, có thể sửa bằng dữ liệu/prompt có mục tiêu.

| Family | Số case fail | Hành vi quan sát được | Rủi ro | Hướng xử lý |
|---|---:|---|---|---|
| `ticket_missing_location` | 3 | Coi thông tin là đủ rồi tạo ticket dù `location` thiếu hoặc `null`; `missing_fields=[]`. | Tạo ticket không đủ dữ liệu và bỏ qua bước clarification. | Thêm ví dụ đối lập: thiếu/`null` location phải trả `ask_clarification`, `missing_fields=["location"]`, không tạo action side effect. Thêm validator trước `create_ticket`. |
| `handbook_grounded` | 3 | Không trả lời theo handbook mà chuyển sang tạo ticket dù câu hỏi là handbook question. | Mất grounding, tạo side effect không cần thiết. | Bổ sung SFT cho answer-from-handbook/citation và negative examples: không có bằng chứng thì clarification, không tự chuyển thành ticket. |
| `announcement_missing_scope` | 2 | Hành vi clarification hợp lý nhưng dùng `missing_fields=["audience"]` thay vì field canonical mà evaluator mong đợi (`scopes`). | Fail contract do synonym/taxonomy, dù UX gần đúng. | Chuẩn hóa output schema: chỉ dùng `scopes`; hoặc thêm normalizer `audience -> scopes` trước evaluator/backend. |
| `announcement_edit` | 2 | Draft nói “cập nhật”, nhưng action lại là `publish_announcement` thay vì update flow. | Có nguy cơ publish sai trạng thái. | Dạy rõ state machine: edit -> `update_announcement`; publish chỉ sau pending update và explicit confirmation. |
| `confirmation_without_pending` | 1 | Action clarification và missing fields đúng, nhưng intent là `clarification` thay vì intent canonical của test. | Chủ yếu là taxonomy/evaluator mismatch, rủi ro hành vi thấp. | Bổ sung intent canonical cho case “confirm nhưng không có pending action”; cân nhắc map intent ở layer hậu xử lý. |

**Đánh giá Qwen:** schema và required-field completion đã rất tốt. Ưu tiên sửa ba lỗi hành vi: chặn ticket thiếu location, handbook grounding, và phân biệt update/publish announcement.

## Phân tích lỗi Gemma 4 E4B

Gemma fail toàn bộ check ở 50/100 case. Lỗi phân bố rộng hơn Qwen, cho thấy contract chưa được internalize ổn định.

| Nhóm lỗi | Family liên quan | Số case fail | Dấu hiệu từ log | Rủi ro / hướng xử lý |
|---|---|---:|---|---|
| Hủy yêu cầu không theo taxonomy canonical | `announcement_cancel` (10), `ticket_cancel` (3) | 13 | Trả các intent biến thể như `cancelled_request`, `cancelled_action`, `cancelled`; action thường `null`. | Chuẩn hóa một intent/action hủy duy nhất; thêm nhiều ví dụ đa ngôn ngữ cho cancel và validator cấm intent ngoài enum. |
| Ticket thiếu dữ liệu hoặc nhiều sự cố | `ticket_multiple_issues` (5), `ticket_missing_category` (5), `ticket_complete` (4), `ticket_correction` (2), `ticket_followup_location` (1) | 17 | Có case hỏi clarification nhưng vẫn phát `create_ticket`; draft/payload không nhất quán (`type` vs `category`), hoặc location bị suy diễn. | Tách rõ “clarify” và “create”; validate required fields từ draft lẫn payload; huấn luyện multi-issue split/choice và correction state. |
| Tin cậy attachment | `ticket_untrusted_attachment` (5), `ticket_trusted_attachment` (3) | 8 | Ví dụ trusted attachment bị nhận nhầm thành handbook question và không tạo ticket. | Bổ sung feature/label cho trusted vs untrusted attachment; đào tạo decision table và test adversarial attachment. |
| Announcement scope, edit và content | `announcement_edit` (4), `announcement_all_residents` (4), `announcement_building` (3), `announcement_missing_content` (1) | 12 | Scope/action announcement chưa nhất quán. | Bổ sung examples phân biệt `all_residents`, building, project, unit; ép state machine update/publish và content-required gate. |

### Các case Gemma đáng chú ý

- `ticket_multiple_issues`: model nói cần clarification nhưng vẫn trả `create_ticket`, đặt `missing_fields=[]` và dùng `draft.type` thay cho `draft.category`. Đây là lỗi contract kép: decision và representation không khớp nhau.
- `ticket_followup_location`: action payload điền `location="phòng ngủ nhỏ"` nhưng draft không có location; không được suy diễn trường định danh địa điểm từ context không chắc chắn.
- `ticket_trusted_attachment`: chuyển ticket request thành `handbook_question` và từ chối quyền tạo ticket. Đây là lỗi role/intent/action nghiêm trọng.
- Các case `announcement_cancel`: nội dung nói đã hủy nhưng intent canonical sai. Đây có thể là lỗi label/enum hơn là UX, song vẫn gây fail tích hợp backend.

## Kế hoạch cải thiện và đánh giá tiếp theo

1. **Giữ Qwen làm ứng viên deploy/benchmark chính.** Sửa data targeted cho 11 failure case, sau đó chạy lại full held-out 600 case.
2. **Nếu tiếp tục Gemma, ưu tiên contract SFT trước.** Bổ sung mẫu cho cancellation enum, required-field gate, ticket clarification vs creation, attachment trust, và announcement scope/state machine. Không nên chỉ tăng epoch vì lỗi đang phân bố theo family.
3. **Harden layer hậu xử lý cho cả hai model.** JSON schema chặt, enum canonical, validator bắt buộc cho ticket/announcement, và state machine chặn publish khi chỉ mới edit.
4. **Báo cáo chính thức.** Chạy `MAX_EVAL_CASES=None`, lưu raw result theo family, rồi so sánh lại cùng seed, generation settings và cùng held-out test set.

## Quyết định hiện tại

- **Chọn Qwen3-4B QLoRA** cho vòng tích hợp tiếp theo.
- **Không chọn Gemma 4 E4B QLoRA ở cấu hình hiện tại** cho agent có action side effect; `action_accuracy` 56% và `all_checks_pass_rate` 50% chưa đủ an toàn.
- Dùng Gemma như nhánh nghiên cứu sau khi sửa dataset contract và chạy lại benchmark đầy đủ.
