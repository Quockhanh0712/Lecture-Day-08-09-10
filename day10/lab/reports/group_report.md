# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** AI In Action - Nhóm 5  
**Thành viên:**
| Tên | MSV / Vai trò | Email |
|-----|------------------|-------|
| Trần Quốc Khánh | 2A202600679 / Ingestion & Cleaning | quockhanh05@gmail.com |

**Ngày nộp:** 2026-06-10  
**Repo:** Quockhanh0712/Lecture-Day-08-09-10  

---

## 1. Tổng quan Kiến trúc Pipeline & Kỹ thuật Vận hành

Hệ thống Data Pipeline của chúng tôi được thiết kế theo mô hình luồng dữ liệu 4 tầng (Ingest → Transform → Validate → Embed) nhằm chuẩn hóa dữ liệu tri thức thô trước khi nạp vào Vector Database.

```
[policy_export_dirty.csv] ──(Ingest)──> [cleaning_rules.py] ──(Cleaned & Quarantine)──> [expectations.py] ──(Validation Gate)──> [PyVi Embedding Function] ──(Embed)──> [(ChromaDB)]
```

### 1.1. Các công nghệ và phương pháp sử dụng:
- **ChromaDB (Persistent Client):** Cơ sở dữ liệu vector cục bộ để lưu trữ và quản lý tài liệu.
- **Sentence-Transformers (`Quockhanh05/Vietnam_legal_embeddings`):** Mô hình học máy nhúng văn bản chuyên dụng cho tiếng Việt pháp lý.
- **PyVi (Vietnamese NLP):** Thư viện tách từ (Word Segmentation) hỗ trợ mô hình nhúng nhận diện ngữ nghĩa chính xác hơn.
- **PyTest:** Khung kiểm thử tự động phục vụ quy trình phát triển hướng kiểm thử (TDD).

### 1.2. Lệnh chạy và Logs:
Chuỗi lệnh chạy toàn trình (End-to-End Ingestion):
```powershell
$env:PYTHONIOENCODING="utf-8"; python etl_pipeline.py run --run-id run-good
```
Mỗi phiên chạy tạo ra một định danh `run_good` duy nhất, xuất bản vết tại [run_run-good.log](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/logs/run_run-good.log) và tệp mô tả tài nguyên [manifest_run-good.json](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/manifests/manifest_run-good.json).

---

## 2. Tiền xử lý dữ liệu (Cleaning) & Bộ kiểm định chất lượng (Expectations)

Nhóm đã phát hiện ra các gaps của pipeline baseline cũ và bổ sung **3 cleaning rules mới** cùng **2 expectations mới** để giải quyết triệt để lỗi dữ liệu:

### 2a. Bảng tác động số liệu (Metric Impact Table)

| Quy tắc / Kiểm định mới | Trạng thái Trước | Trạng thái Sau / Khi Inject lỗi | Minh chứng Kỹ thuật |
|-------------------------|------------------|---------------------------------|---------------------|
| **Whitelist `access_control_sop`** | 0 dòng được duyệt, 4 dòng bị cách ly | 2 dòng sạch được duyệt nạp | [quarantine_run-good.csv](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/quarantine/quarantine_run-good.csv) |
| **Loại bỏ tiền tố nhiễu (`Nội dung không rõ ràng:`, `!!!`)** | Chứa nguyên các chuỗi nhiễu, làm sai lệch phân phối vector nhúng | Cắt tỉa sạch sẽ khỏi đầu chunk văn bản thô | [cleaned_run-good.csv](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/cleaned/cleaned_run-good.csv) |
| **Quarantine tri thức stale của HR** | Nạp nhầm 1 dòng phép năm cũ (10 ngày) có ngày hiệu lực giả 2026 | Cách ly 1 dòng vi phạm (`stale_hr_policy_content`) | [quarantine_run-good.csv](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/quarantine/quarantine_run-good.csv) |
| **E7: Kiểm định tiền tố `"Nội dung không rõ ràng:"`** | Không kiểm tra | Báo `FAIL (halt)` nếu bước làm sạch bỏ sót | [run_inject-bad.log](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/logs/run_inject-bad.log) |
| **E8: Kiểm định tiền tố `"!!!"`** | Không kiểm tra | Báo `FAIL (halt)` nếu bước làm sạch bỏ sót | [run_inject-bad.log](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/artifacts/logs/run_inject-bad.log) |

### 2b. Chi tiết Kỹ thuật về Expectations (Validation):
Chúng tôi thiết lập mức độ nghiêm trọng `severity="halt"` cho E7 và E8. Khi chạy thử nghiệm ở chế độ inject lỗi (`--no-refund-fix`), hệ thống phát hiện lỗi và lập tức ngắt tiến trình (`PIPELINE_HALT`), chặn đứng không cho phép đẩy dữ liệu lỗi vào Vector DB.

---

## 3. Ảnh hưởng đến Truy xuất ngữ nghĩa (Before vs After Retrieval)

Chúng tôi đã thiết lập kịch bản làm hỏng dữ liệu thông qua lệnh:
```powershell
$env:PYTHONIOENCODING="utf-8"; python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate
```

### So sánh định lượng kết quả truy vấn (Retrieval Evidence):

- **Trước khi sửa đổi (Bản lỗi - `after_inject_bad.csv`):**
  - Câu hỏi `q_refund_window` trả về chunk chứa `"14 ngày làm việc"`.
  - Kết quả đánh giá: `contains_expected: no`, `hits_forbidden: yes`.
- **Sau khi sửa đổi (Bản sạch - `eval_after_fix.csv`):**
  - Câu hỏi `q_refund_window` trả về chunk đã được chuẩn hóa tự động: `"7 ngày làm việc. [cleaned: stale_refund_window]"`.
  - Kết quả đánh giá: `contains_expected: yes`, `hits_forbidden: no`, `top1_doc_expected: yes`.
  - Bộ câu hỏi chấm điểm chính thức của giảng viên (`grading_run.py`) đạt điểm tuyệt đối **10/10** trên cả 10 câu hỏi.

---

## 4. Freshness SLA & Giám sát (Monitoring)

Chúng tôi áp dụng cấu hình Freshness SLA là **24 giờ** tính từ thời điểm xuất dữ liệu nguồn (`exported_at`).
- Do tệp CSV mẫu tĩnh có ngày xuất lớn nhất là `2026-04-10`, nên hệ thống báo trạng thái `freshness_check=FAIL` (quá hạn hơn 1400 giờ).
- Điều này chứng minh hệ thống giám sát hoạt động chuẩn xác. Khi triển khai thực tế trên Production với luồng nạp tự động hàng ngày, chỉ số này sẽ tự động chuyển sang `PASS`.

---

## 5. Tích hợp với RAG Agent (Day 09)

Dữ liệu sạch sau khi được nạp vào collection `day10_kb` đóng vai trò là kho tri thức tối hậu cho các Agent. Chúng tôi viết một Custom Embedding Function kế thừa của ChromaDB để nhúng và truy vấn:
```python
class PyViSentenceTransformerEmbeddingFunction(embedding_functions.SentenceTransformerEmbeddingFunction):
    def __call__(self, input):
        try:
            from pyvi import ViTokenizer
            segmented = [ViTokenizer.tokenize(doc) for doc in input]
        except ImportError:
            segmented = input
        return super().__call__(segmented)
```
**Ưu thế kỹ thuật:** Tách từ `pyvi` chỉ diễn ra khi tính toán vector (trong bộ nhớ), văn bản lưu thực tế trong ChromaDB vẫn là tiếng Việt chuẩn. Điều này giúp Agent Day 09 nhận được ngữ cảnh sạch để trả lời người dùng mà không bị lẫn các dấu gạch dưới (`_`).

---

## 6. Các lưu ý quan trọng khi vận hành (Operational Notes)

1. **Thư mục làm việc:** Phải thực thi lệnh từ thư mục `day10/lab`. Nếu đứng ở thư mục gốc của repo, chương trình sẽ báo lỗi không tìm thấy đường dẫn file.
2. **Mã hóa Console (Windows):** Phải đặt biến môi trường `$env:PYTHONIOENCODING="utf-8"` trên PowerShell trước khi chạy để tránh lỗi crash chương trình do in các ký tự unicode tiếng Việt ra terminal.
3. **Hiện tượng nghẽn tải Model:** Lần chạy đầu tiên sẽ tải model `Quockhanh05/Vietnam_legal_embeddings` từ Hugging Face (~90MB). Không được tắt ngang tiến trình (`Ctrl+C`) vì sẽ làm hỏng file cache của thư mục Hugging Face.
4. **Không skip validate trên Production:** Tránh sử dụng cờ `--skip-validate` vì nó sẽ vô hiệu hóa chốt chặn chất lượng dữ liệu, cho phép dữ liệu stale lọt vào Vector DB.
