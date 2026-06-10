# Data contract — Lab Day 10

Tài liệu này đặc tả Data Contract phục vụ cho tầng lưu trữ tri thức hỗ trợ CS và IT Helpdesk.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| **policy_refund_v4** | CSV batch export định kỳ | Chứa thông tin hoàn tiền cũ (14 ngày làm việc) | Alert nếu phát hiện chuỗi "14 ngày làm việc" sau clean |
| **sla_p1_2026** | CSV batch export định kỳ | Thiếu thông tin hoặc không parse được ngày hiệu lực | Alert nếu số bản ghi = 0 |
| **it_helpdesk_faq** | API sync hoặc CSV upload | Chứa các đoạn text nháp có marker "Nội dung không rõ ràng:" hoặc "!!!" | Chặn (Halt) nếu phát hiện tiền tố rác sau clean |
| **hr_leave_policy** | Portal HR export | Bản ghi phép năm cũ (10 ngày phép) bị cài cắm effective_date giả năm 2026 | Đẩy vào quarantine; cảnh báo nếu phát hiện "10 ngày phép năm" |
| **access_control_sop**| SOP security document | Không thuộc Whitelist cũ nên bị drop toàn bộ | Quarantine nếu ID không có trong allowed list |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| **chunk_id** | string | Có | Khóa chính duy nhất của mỗi chunk, cấu trúc: `{doc_id}_{seq}_{hash}` |
| **doc_id** | string | Có | Mã định danh tài liệu gốc (phải khớp `allowed_doc_ids` trong data contract) |
| **chunk_text**| string | Có | Nội dung văn bản đã làm sạch sạch (không chứa prefix nhiễu, min_length >= 8) |
| **effective_date** | date | Có | Ngày hiệu lực của tài liệu, định dạng chuẩn ISO `YYYY-MM-DD` |
| **exported_at** | datetime | Có | Thời điểm dữ liệu được xuất từ hệ thống nguồn |

---

## 3. Quy tắc quarantine vs drop

- **Quarantine (Cách ly):** Bất kỳ dòng dữ liệu nào vi phạm các quy tắc như: sai định dạng ngày hiệu lực, không thuộc danh mục tài liệu cho phép, chứa dữ liệu stale hoặc chunk_text trống sẽ bị chuyển sang thư mục `artifacts/quarantine/` kèm theo cột `reason`.
- **Drop (Bỏ qua):** Các bản ghi trùng lặp hoàn toàn về mặt ngữ nghĩa (sau khi đã chuẩn hóa) sẽ bị drop (chỉ giữ lại bản ghi đầu tiên ghi nhận) và đánh dấu là trùng lặp (`duplicate_chunk_text`).
- **Phê duyệt & Tái nạp:** Các dữ liệu trong quarantine cần được Data Ops Team kiểm tra định kỳ, liên hệ với bên cung cấp dữ liệu để đính chính và tái nạp lại bằng một file sửa đổi.

---

## 4. Phiên bản & canonical

- **Source of truth cho policy refund:** File gốc `data/docs/policy_refund_v4.txt` quy định thời hạn hoàn tiền tối đa là 7 ngày làm việc. Bất kỳ văn bản nào đề xuất 14 ngày làm việc đều là stale và phải được chuyển đổi hoặc cách ly.
- **Source of truth cho HR Leave Policy:** File gốc `data/docs/hr_leave_policy.txt` (chính sách 2026) quy định số ngày phép năm là 12 ngày cho nhân viên dưới 3 năm kinh nghiệm. Dữ liệu chứa 10 ngày phép là stale.
- **Source of truth cho Access Control:** File gốc `data/docs/access_control_sop.txt` quy định các cấp quyền và quy trình tương ứng.
