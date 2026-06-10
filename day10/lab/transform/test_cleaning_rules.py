import pytest
from transform.cleaning_rules import clean_rows
from quality.expectations import run_expectations

def test_access_control_sop_allowed():
    # Arrange
    rows = [
        {
            "doc_id": "access_control_sop",
            "chunk_text": "Quy trình cấp quyền truy cập hệ thống.",
            "effective_date": "2026-01-01",
            "exported_at": "2026-01-02",
        }
    ]
    
    # Act
    cleaned, quarantine = clean_rows(rows)
    
    # Assert
    assert len(cleaned) == 1, "access_control_sop should be allowed"
    assert len(quarantine) == 0, f"access_control_sop should not be quarantined: {quarantine}"
    assert cleaned[0]["doc_id"] == "access_control_sop"


def test_strip_noisy_prefixes():
    # Arrange
    rows = [
        {
            "doc_id": "it_helpdesk_faq",
            "chunk_text": "Nội dung không rõ ràng: Cách đặt lại mật khẩu Wifi.",
            "effective_date": "2026-01-01",
            "exported_at": "2026-01-02",
        },
        {
            "doc_id": "it_helpdesk_faq",
            "chunk_text": "!!! Cần liên hệ admin",
            "effective_date": "2026-01-01",
            "exported_at": "2026-01-02",
        }
    ]
    
    # Act
    cleaned, quarantine = clean_rows(rows)
    
    # Assert
    assert len(cleaned) == 2
    assert len(quarantine) == 0
    assert cleaned[0]["chunk_text"] == "Cách đặt lại mật khẩu Wifi.", "Should strip 'Nội dung không rõ ràng:' and strip spaces"
    assert cleaned[1]["chunk_text"] == "Cần liên hệ admin", "Should strip '!!!' and strip spaces"


def test_quarantine_stale_hr_policy_content():
    # Arrange
    rows = [
        {
            "doc_id": "hr_leave_policy",
            "chunk_text": "Quy định cũ có 10 ngày phép năm.",
            "effective_date": "2026-01-01", # 2026 date but stale content
            "exported_at": "2026-01-02",
        }
    ]
    
    # Act
    cleaned, quarantine = clean_rows(rows)
    
    # Assert
    assert len(cleaned) == 0, "Stale HR policy content should be filtered out"
    assert len(quarantine) == 1, "Stale HR policy content should be quarantined"
    assert quarantine[0]["reason"] == "stale_hr_policy_content"


def test_expectations_halt_on_noisy_markers():
    # Arrange
    cleaned_rows_with_noisy_prefix_1 = [
        {
            "chunk_id": "doc1_1",
            "doc_id": "it_helpdesk_faq",
            "chunk_text": "Nội dung không rõ ràng: Lỗi kết nối",
            "effective_date": "2026-01-01",
        }
    ]
    
    cleaned_rows_with_noisy_prefix_2 = [
        {
            "chunk_id": "doc2_1",
            "doc_id": "it_helpdesk_faq",
            "chunk_text": "!!! Lỗi bảo mật",
            "effective_date": "2026-01-01",
        }
    ]
    
    # Act
    results_1, halt_1 = run_expectations(cleaned_rows_with_noisy_prefix_1)
    results_2, halt_2 = run_expectations(cleaned_rows_with_noisy_prefix_2)
    
    # Assert
    # Check expectation 7 (for "Nội dung không rõ ràng:")
    exp_7_results_1 = [r for r in results_1 if r.name == "no_noisy_unclear_content_prefix"]
    assert len(exp_7_results_1) == 1
    assert exp_7_results_1[0].passed is False
    assert exp_7_results_1[0].severity == "halt"
    assert halt_1 is True
    
    # Check expectation 8 (for "!!!")
    exp_8_results_2 = [r for r in results_2 if r.name == "no_exclamation_noise_prefix"]
    assert len(exp_8_results_2) == 1
    assert exp_8_results_2[0].passed is False
    assert exp_8_results_2[0].severity == "halt"
    assert halt_2 is True
