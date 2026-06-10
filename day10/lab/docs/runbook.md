# Runbook — Lab Day 10

Sổ tay xử lý sự cố chất lượng dữ liệu tri thức.

---

## 1. Symptom (Triệu chứng)

- Người dùng cuối hoặc AI Agent trả lời sai thông tin chính sách hoàn tiền (ví dụ: trả lời khách hàng được hoàn tiền trong vòng "14 ngày" thay vì "7 ngày").
- Nhân viên phản ánh AI báo họ chỉ được "10 ngày phép năm" (thông tin cũ 2025) thay vì "12 ngày phép năm" (chính sách mới 2026).
- Thiếu các câu trả lời liên quan đến quy trình cấp quyền truy cập quản trị Level 4.

---

## 2. Detection (Phát hiện)

Sự cố được phát hiện tự động qua các kênh:
- **Quality Alert:** Pipeline chạy bị dừng lại (`PIPELINE_HALT`) do kiểm thử chất lượng (Expectations) trả về kết quả thất bại (ví dụ: `refund_no_stale_14d_window` báo có vi phạm).
- **Retrieval Eval Alert:** Script `eval_retrieval.py` báo cột `hits_forbidden` bằng `yes` hoặc `contains_expected` bằng `no`.
- **Freshness SLA Alert:** Kiểm tra manifest hàng ngày báo `freshness_check=FAIL` (dữ liệu không cập nhật quá 24 giờ).

---

## 3. Diagnosis (Chẩn đoán)

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| **1** | Kiểm tra file manifest gần nhất tại `artifacts/manifests/` | Xác định xem pipeline có bị skip validation không (`skipped_validate` có bằng `true`?) và `run_id` tương ứng là gì. |
| **2** | Mở file cách ly gần nhất tại `artifacts/quarantine/` | Xem danh sách các bản ghi bị loại bỏ và cột `reason` (ví dụ: `stale_hr_policy_content`, `unknown_doc_id`). |
| **3** | Chạy kiểm tra retrieval nhanh | Chạy lệnh `$env:PYTHONIOENCODING="utf-8"; python eval_retrieval.py` để xem các câu hỏi nào đang bị lỗi retrieval hoặc dính chunk rác. |

---

## 4. Mitigation (Khắc phục tạm thời)

1. **Khôi phục nhanh (Rollback):** Nếu dữ liệu mới nạp làm hỏng kết quả truy vấn, tiến hành khôi phục collection Chroma về snapshot an toàn trước đó bằng cách chạy lại pipeline với file raw export của ngày hôm trước.
2. **Cập nhật thủ công:** Nếu có lỗi dịch thuật hoặc dữ liệu stale chưa được lọc sạch trong DB, tiến hành xóa trực tiếp chunk ID lỗi ra khỏi Chroma DB qua script admin hoặc chạy pipeline chuẩn không có cờ `--skip-validate`.
3. **Thông báo hệ thống:** Bật banner tạm thời cảnh báo dữ liệu đang được đồng bộ hóa lại trên giao diện CS Portal.

---

## 5. Prevention (Phòng ngừa lâu dài)

1. **Hạn chế skip validate:** Cấm sử dụng tham số `--skip-validate` trong môi trường Production. Mọi lỗi Quality Gate phải được giải quyết triệt để trước khi embed.
2. **Bảo trì Whitelist:** Khi bổ sung tài liệu mới, Data Team phải đồng thời cập nhật `ALLOWED_DOC_IDS` trong `cleaning_rules.py` và `contracts/data_contract.yaml`.
3. **Cập nhật bộ lọc rác định kỳ:** Theo dõi các từ khóa nhiễu phát sinh mới để cập nhật hàm làm sạch text và bổ sung Expectation tương ứng để ngăn chặn dữ liệu rác lọt vào Vector DB.
