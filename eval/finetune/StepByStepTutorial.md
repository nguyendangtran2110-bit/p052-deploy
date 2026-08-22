# Fine-tune Qwen3-4B bằng QLoRA trên Kaggle

Tài liệu này chạy cùng notebook `finetune.ipynb`. Mục tiêu là fine-tune
`Qwen/Qwen3-4B` cho structured agent của OnBxrd: phân loại intent, trích xuất
draft, phát hiện trường thiếu và đề xuất action cần xác nhận.

## 1. Điều kiện trước khi bắt đầu

1. Tạo hoặc đăng nhập Kaggle.
2. Tạo Hugging Face account. `Qwen/Qwen3-4B` hiện không yêu cầu token để tải,
   nhưng nên tạo token `read` để tránh giới hạn tải model trong tương lai.
3. Tại project local, đảm bảo dataset đã được sinh và kiểm tra:

```powershell
.\.venv\Scripts\python.exe scripts\generate_ai_finetune_dataset.py
.\.venv\Scripts\python.exe scripts\validate_ai_finetune_dataset.py
```

Kết quả cần có `Validation: PASS` và các file trong `eval/finetune/`.

## 2. Tạo Kaggle Dataset từ dữ liệu hiện có

Không upload `.env`, API key, presigned URL, dữ liệu resident thật hoặc file
S3 thật. Chỉ upload thư mục sau:

```text
eval/finetune/
  canonical/train.jsonl
  canonical/validation.jsonl
  canonical/test.jsonl
  openai/train.jsonl
  README.md
```

Trên Kaggle:

1. Chọn `Create` -> `New Dataset`.
2. Upload thư mục `eval/finetune`.
3. Đặt tên dễ nhận biết, ví dụ `onbxrd-agent-finetune-v1`.
4. Bấm `Create`.

Kaggle sẽ gắn dataset vào path dạng:

```text
/kaggle/input/onbxrd-agent-finetune-v1/
```

Notebook tự dò file `canonical/train.jsonl`, nên tên slug không cần trùng ví
dụ trên.

## 3. Tạo Kaggle Notebook

1. Chọn `Create` -> `New Notebook`.
2. Trong `Notebook options`, chọn accelerator GPU. Ưu tiên T4 hoặc P100 16 GB.
3. Bật `Internet` vì notebook cần tải LLaMA-Factory và model từ Hugging Face.
4. Chọn `Add Input`, tìm và thêm dataset ở bước 2.
5. Upload hoặc copy nội dung file `eval/finetune/finetune.ipynb` vào notebook.
6. Lưu một bản copy riêng trước khi chạy để giữ notebook nguồn không có output.

Qwen3-4B QLoRA phù hợp GPU 16 GB. Không tăng `cutoff_len` lên 8K trong lần
đầu; cấu hình `2048`, batch size `1` và gradient accumulation trong notebook
là điểm khởi đầu an toàn hơn.

## 4. Chạy notebook theo thứ tự

Chạy cell lần lượt, không chạy cell train trước các cell chuẩn bị dữ liệu.

1. **Giới thiệu và cấu hình:** kiểm tra GPU, khai báo path, run name và model.
2. **Cài LLaMA-Factory:** clone framework, cài dependency và xác nhận CLI.
3. **Kiểm tra dữ liệu:** notebook tìm file input, kiểm tra số mẫu và đọc system
   prompt đang dùng trong file OpenAI JSONL.
4. **Chuyển dữ liệu:** canonical JSONL được chuyển thành ShareGPT chat data.
   Assistant target là JSON của `AgentStructuredResult`, không phải prose.
5. **Kiểm tra dataset:** xem mẫu train và validation trước khi train. Nếu JSON
   bị sai, dừng ở đây và sửa generator local thay vì sửa tay dữ liệu Kaggle.
6. **Sinh YAML:** tạo `qwen3_qlora_sft.yaml` với QLoRA 4-bit.
7. **Train:** chạy `llamafactory-cli train`. Adapter xuất ra
   `/kaggle/working/onbxrd-qwen3-4b-qlora-v1/adapter`.
8. **Theo dõi loss:** đọc `trainer_state.json` và kiểm tra loss không diverge.
9. **Inference smoke test:** kiểm tra model trả JSON hợp lệ cho một ticket và
   một announcement.
10. **Held-out evaluation:** chạy trước với 100 test cases. Nếu đạt ngưỡng,
    đặt `MAX_EVAL_CASES = None` để chạy toàn bộ 600 case.
11. **Benchmark base và fine-tuned:** notebook giải phóng adapter, load lại
    Qwen3-4B base và chạy trên đúng cùng test cases, cấu hình generation và
    system prompt. Kết quả có bảng delta cùng case cải thiện/regression.
12. **Đóng gói adapter:** tạo ZIP để tải về hoặc đưa lên Hugging Face/Kaggle
    Model. Không merge adapter trong lần thử đầu.

## 5. Cấu hình QLoRA được dùng và cách điều chỉnh

| Tham số | Giá trị ban đầu | Khi nào điều chỉnh |
|---|---:|---|
| `quantization_bit` | `4` | Giữ nguyên trên GPU 16 GB. |
| `lora_rank` | `16` | Tăng `32` chỉ sau khi eval cho thấy underfit. |
| `lora_alpha` | `32` | Giữ tỷ lệ xấp xỉ 2 lần rank. |
| `learning_rate` | `1e-4` | Giảm `5e-5` nếu validation loss tăng rõ. |
| `num_train_epochs` | `3` | Thử 1, 2, 3 epoch; không chọn chỉ theo train loss. |
| `cutoff_len` | `2048` | Giảm `1536/1024` nếu OOM; chỉ tăng khi đo được context bị cắt. |
| `gradient_accumulation_steps` | `8` | Tăng nếu muốn effective batch lớn hơn mà không OOM. |

Với dataset synthetic hiện tại, không nên train nhiều epoch chỉ để loss thấp.
Tiêu chí chọn checkpoint là held-out `all-checks pass rate`, schema-valid rate,
intent accuracy, action accuracy và required-field completion.

## 6. Đọc kết quả evaluation

Notebook xuất kết quả fine-tuned vào `evaluation_results.json` /
`evaluation_summary.json`, kết quả base vào `base_evaluation_results.json` /
`base_evaluation_summary.json` và bảng chênh lệch vào
`benchmark_comparison.json`.

- `schema_valid_rate`: tỷ lệ model trả về JSON parse được và đủ key contract.
- `intent_accuracy`: intent đúng so với expected.
- `action_accuracy`: action type đúng, bao gồm `null` khi không được action.
- `required_field_completion`: draft chứa đủ trường khi case yêu cầu tạo ticket
  hoặc announcement.
- `average_quality_score`: trung bình tỷ lệ các kiểm tra pass trong từng case.
  Một case có thể đúng intent nhưng sai action hoặc thiếu draft, nên điểm này vẫn
  có ích để chẩn đoán.
- `all_checks_pass_rate`: tỷ lệ case pass toàn bộ kiểm tra. Đây là tiêu chí chấp
  nhận chính vì một action sai có thể tạo workflow sai.

So sánh adapter với base Qwen3-4B trên cùng `test.jsonl`. Notebook chạy hai
model tuần tự để không giữ cả hai trong GPU memory. Một benchmark đầy đủ 600
case sẽ cần thời gian gần gấp đôi evaluation đơn lẻ. Chỉ xem fine-tune là có ích
nếu `all-checks pass rate` tăng, safety không giảm và các regression case được
review được giải thích được.

## 7. Ngưỡng quyết định khuyến nghị

Đây là ngưỡng thử nghiệm để quyết định có tiếp tục data work hay không, không
phải cam kết chất lượng production:

| Metric | Mốc nên hướng tới |
|---|---:|
| Schema-valid rate | >= 98% |
| Intent accuracy | >= 92% |
| Action accuracy | >= 90% |
| Required-field completion | >= 90% |
| All-checks pass rate | >= 85% |

Nếu schema-valid thấp, ưu tiên bổ sung case JSON/confirmation sai và giảm
temperature về `0` khi inference. Nếu intent/action thấp, bổ sung những case
thất bại đã được review vào **train hoặc validation**, không đưa vào held-out
test. Nếu ticket/announcement draft thiếu trường, bổ sung multi-turn case cho
chính trường đó.

## 8. Tải và sử dụng adapter

Sau khi train, tải file ZIP ở `/kaggle/working/<run-name>/`. Adapter gồm tối
thiểu `adapter_model.safetensors` và `adapter_config.json`.

Để phục vụ local, cần chạy base model Qwen3-4B cùng adapter bằng Transformers,
vLLM hoặc engine tương thích PEFT. Backend hiện tại vẫn là nơi giữ RBAC,
trusted attachment IDs, confirmation boundary và thực thi action; adapter chỉ
thay thế lớp suy luận LLM.

Không thay `OPENAI_API_KEY` hay Groq model hiện tại chỉ vì adapter đã train.
Hãy tạo một provider/config riêng cho Qwen và chuyển traffic thử nghiệm qua
feature flag sau khi benchmark.

## 9. Các lỗi thường gặp

### Hết GPU memory

Giảm `cutoff_len` xuống `1536` hoặc `1024`, giữ batch size `1`, tăng gradient
accumulation nếu cần. Đảm bảo `quantization_bit: 4` và
`gradient_checkpointing: true`.

### Không tải được model hoặc GitHub

Kiểm tra Internet đã bật. Nếu Kaggle giới hạn mạng, thêm model hoặc source code
vào Kaggle Dataset trước, rồi sửa `MODEL_NAME_OR_PATH` thành path trong
`/kaggle/input/...`.

### LLaMA-Factory báo không tìm thấy dataset

Kiểm tra `dataset_dir`, `dataset_info.json` và tên dataset trong YAML phải cùng
là `onbxrd_agent_train` / `onbxrd_agent_validation`. Chạy lại cell chuyển đổi,
không sửa file JSON thủ công.

### Model trả prose thay vì JSON

Kiểm tra template phải là `qwen3_nothink`, system prompt được đọc từ dataset và
inference để `do_sample=False`, `temperature=0`. Bổ sung các failed cases đã
review, nhất là confirm/cancel/missing fields, rồi fine-tune lại.

### Validation tốt nhưng held-out test kém

Không chỉnh test set. Kiểm tra test bị khác distribution nào, tạo case mới từ
thất bại cho train/validation và chạy lại với run name mới.

## 10. Phần không nằm trong notebook này

Notebook chưa tự deploy Qwen vào Docker/backend, chưa merge adapter vào base
model, chưa upload Hugging Face Hub và chưa chạy OpenAI/Groq benchmark có tính
phí. Các bước đó nên thực hiện sau khi held-out evaluation đạt ngưỡng và có
review con người cho các lỗi còn lại.
