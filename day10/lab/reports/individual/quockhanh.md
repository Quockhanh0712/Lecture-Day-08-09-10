# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trần Quốc Khánh - 2A202600679  
**Vai trò:** Ingestion & Cleaning Owner  
**Ngày nộp:** 2026-06-10  

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

Trong dự án Lab Day 10, tôi chịu trách nhiệm chính về phần **Ingestion & Cleaning**:
- Tôi đã trực tiếp sửa đổi và mở rộng file [cleaning_rules.py](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/transform/cleaning_rules.py) để bổ sung 3 cleaning rules mới: thêm `access_control_sop` vào whitelist, dọn dẹp các tiền tố nhiễu rác ở đầu chunk (`Nội dung không rõ ràng:` và `!!!`), và lọc các bản ghi phép năm cũ 10 ngày của HR (`stale_hr_policy_content`).
- Tôi đã thiết kế và triển khai file kiểm thử tự động [test_cleaning_rules.py](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/transform/test_cleaning_rules.py) theo đúng quy trình TDD (Red-Green-Refactor).
- Tôi đã làm việc cùng với nhóm để đảm bảo các expectations trong [expectations.py](file:///a:/AIK20_aithucchien/Lecture-Day-08-09-10/day10/lab/quality/expectations.py) đồng bộ hoàn toàn với các rules biến đổi này.

---

## 2. Quyết định kỹ thuật & Tích hợp công nghệ (100–150 từ)

Một quyết định kỹ thuật quan trọng của tôi là **thiết kế Custom Embedding Function tích hợp tách từ `pyvi`**:
- Tôi tiến hành tạo class `PyViSentenceTransformerEmbeddingFunction` kế thừa trực tiếp từ class `SentenceTransformerEmbeddingFunction` của thư viện ChromaDB.
- Tôi ghi đè (override) phương thức `__call__` để thực hiện chuyển đổi văn bản sang dạng tách từ bằng `ViTokenizer.tokenize(doc)` trước khi truyền vào phương thức nhúng của lớp cha.
- **Ý nghĩa:** Giải pháp này giúp mô hình nhúng `Quockhanh05/Vietnam_legal_embeddings` đạt hiệu năng so khớp vector tối ưu nhất nhờ cấu trúc ngữ pháp tiếng Việt đã được chuẩn hóa. Đặc biệt, nó không lưu trữ các ký tự gạch dưới `_` vào cơ sở dữ liệu vật lý của ChromaDB, giúp dữ liệu cung cấp cho RAG Agent Day 09 hoàn toàn sạch sẽ và tự nhiên.

Bên cạnh đó, tôi lựa chọn cấu hình mức độ nghiêm trọng `halt` cho hai quy tắc kiểm định E7 và E8, bắt buộc dừng pipeline ngay lập tức nếu bước làm sạch bỏ sót các tiền tố rác, ngăn không cho dữ liệu lỗi làm ô nhiễm database.

---

## 3. Sự cố và xử lý bất thường (Anomaly Handling) (100–150 từ)

Tôi đã phát hiện ra lỗi **HR Leave Policy Version Conflict** trong dữ liệu thô. 

*Triệu chứng:* Bản ghi phép năm của nhân viên dưới 3 năm kinh nghiệm trong CSV thô có chứa nội dung cũ "10 ngày phép năm" (nội quy năm 2025) nhưng lại được cài cắm `effective_date` giả là `2026-01-01` để vượt qua bộ lọc ngày hiệu lực cơ bản của hệ thống.
*Cách xử lý:* Tôi đã bổ sung thêm một bộ lọc nội dung trong hàm `clean_rows` của `cleaning_rules.py`:
```python
if doc_id == "hr_leave_policy" and "10 ngày phép năm" in fixed_text:
    quarantine.append({**raw, "reason": "stale_hr_policy_content"})
    continue
```
Quy tắc này đã giúp cô lập và chuyển hướng thành công bản ghi lỗi thời này sang tệp quarantine với lý do `stale_hr_policy_content`.

---

## 4. Bằng chứng kiểm thử trước / sau (80–120 từ)

Dưới đây là so sánh kết quả truy vấn cho câu hỏi hoàn tiền (`q_refund_window`) trên hai phiên chạy của database:

- **Trước (`run_id: inject-bad`):**
  `q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi đơn được xác nhận?,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn.,no,yes,yes,3`
  *(Bị dính lỗi hoàn tiền 14 ngày, `hits_forbidden=yes`)*

- **Sau (`run_id: run-good`):**
  `q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi đơn được xác nhận?,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 7 ngày làm việc kể từ xác nhận đơn. [cleaned: stale_refund_window],yes,no,yes,3`
  *(Đã sửa đổi thành công thành 7 ngày, `hits_forbidden=no`)*

---

## 5. Lưu ý quan trọng khi vận hành & Cải tiến (40–80 từ)

1. **Thư mục chạy:** Phải luôn đứng ở thư mục `day10/lab` khi thực thi code.
2. **Mã hóa Console:** Cần đặt `$env:PYTHONIOENCODING="utf-8"` trên PowerShell trước khi chạy để tránh lỗi crash do in tiếng Việt có dấu ra console Windows.
3. **Model Download:** Lần đầu chạy sẽ tải model nhúng (~90MB). Cần đảm bảo đường truyền ổn định và không ngắt tiến trình bằng `Ctrl+C` giữa chừng để tránh lỗi cache.
4. **Cải tiến:** Nếu có thêm 2 giờ, tôi sẽ viết script tự động ánh xạ cấu hình ngày hiệu lực từ file `data_contract.yaml` vào code để tránh kiểm tra cứng chuỗi ký tự ngày tháng.
