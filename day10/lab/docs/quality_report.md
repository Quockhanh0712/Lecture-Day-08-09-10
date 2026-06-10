# Quality report — Lab Day 10

**run_id:** run-good  
**Ngày:** 2026-06-10

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (inject-bad) | Sau (run-good) | Ghi chú |
|--------|---------------------|----------------|---------|
| **raw_records** | 247 | 247 | Tổng số dòng đọc từ file raw CSV |
| **cleaned_records** | 36 | 36 | Số dòng sạch được giữ lại để embed |
| **quarantine_records** | 211 | 211 | Số dòng bị cách ly do lỗi định dạng / stale |
| **Expectation halt?** | **YES** (FAIL E3) | **NO** (ALL PASSED) | Trạng thái dừng của bộ Expectations kiểm định chất lượng |

---

## 2. Before / after retrieval (Minh chứng kiểm thử)

### Câu hỏi: `q_refund_window` (Chính sách hoàn tiền hiện hành)

- **Trước (Bị lỗi - `after_inject_bad.csv`):**
  `q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi đơn được xác nhận?,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn.,no,yes,yes,3`
  - *Nhận xét:* Dữ liệu tri thức bị lỗi "14 ngày" cũ lọt vào index, khiến `hits_forbidden` bị đánh dấu là `yes` và `contains_expected` bị đánh dấu là `no`.

- **Sau (Đã fix - `eval_after_fix.csv`):**
  `q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi đơn được xác nhận?,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 7 ngày làm việc kể từ xác nhận đơn. [cleaned: stale_refund_window],yes,no,yes,3`
  - *Nhận xét:* Chế độ tự động sửa đổi của pipeline đã biến đổi "14 ngày" cũ thành "7 ngày" hiện hành, giúp kết quả tìm kiếm ngữ nghĩa trùng khớp hoàn hảo (`contains_expected=yes`, `hits_forbidden=no`).

### Câu hỏi: `q_hr_annual_leave_under3` (Chính sách phép năm HR)

- **Trước:**
  (Nếu không sửa đổi pipeline, dữ liệu stale 2025 chứa "10 ngày phép năm" sẽ bị nạp do có effective_date 2026 giả mạo, làm nhiễu top-1).

- **Sau:**
  `q_hr_annual_leave_under3,Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm?,hr_leave_policy,Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026.,yes,no,yes,3`
  - *Nhận xét:* Pipeline chủ động cách ly (`stale_hr_policy_content`) các dòng chứa phép năm cũ 10 ngày trong `hr_leave_policy`, giúp ChromaDB chỉ trả về chính xác chunk 12 ngày phép của năm 2026.

---

## 3. Freshness & monitor

- **Kết quả `freshness_check`:** `FAIL`
- **Chi tiết:**
  `{"latest_exported_at": "2026-04-10T00:00:00", "age_hours": 1469.365, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}`
- **Giải thích:** Dữ liệu raw mẫu có timestamp `exported_at` lớn nhất là `2026-04-10`, tính đến thời điểm chạy hiện tại đã vượt quá SLA 24 giờ. Trạng thái `FAIL` này là hoàn toàn chính xác đối với dữ liệu giả lập tĩnh. Trong môi trường thực tế, nếu dữ liệu nguồn được xuất và nạp hàng ngày, chỉ số này sẽ tự động chuyển sang `PASS`.

---

## 4. Corruption inject (Sprint 3)

- **Mô tả hành vi inject:** Chúng tôi sử dụng cờ `--no-refund-fix` để tắt rule làm sạch cửa sổ hoàn tiền của `policy_refund_v4` (giữ nguyên chuỗi "14 ngày làm việc") và sử dụng `--skip-validate` để bỏ qua việc dừng pipeline khi bộ kiểm thử chất lượng phát hiện ra lỗi này.
- **Cách phát hiện:** Bộ Expectation của chúng tôi lập tức bắt được lỗi thông qua quy tắc `refund_no_stale_14d_window` báo trạng thái `FAIL (halt) :: violations=1`. Nếu không skip validation, pipeline sẽ kết thúc với exit code 2 và không thực hiện nạp dữ liệu rác vào ChromaDB.

---

## 5. Hạn chế & việc chưa làm

- Chưa triển khai cảnh báo tự động qua Slack webhook thực tế khi freshness hoặc expectations bị fail (hiện tại chỉ log ra console/manifest).
- Bộ đếm thời gian cho freshness hiện đang được tính dựa trên thời điểm chạy pipeline cục bộ thay vì thời điểm xuất phát từ DB nguồn chính.
