"""HTTP tests for the text-processing endpoint."""

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)

TEXT = """Shipper: ABC Trading
Consignee: XYZ Ltd
Notify Party: XYZ Ltd
Port of Loading: Singapore
Port of Discharge: Mersin
Container Count: 3
Gross Weight: 22,000 KG
"""


def payload():
    return {
        "email": {
            "email_id": "api_test",
            "from": "demo@example.com",
            "subject": "",
            "body": "Please compare the BL against the SI.",
            "attachments": ["si.txt", "bl.txt"],
        },
        "si": {
            "document_id": "si_001",
            "attachment_path": "si.txt",
            "text": TEXT,
        },
        "bl": {
            "document_id": "bl_001",
            "attachment_path": "bl.txt",
            "text": TEXT.replace("Container Count: 3", "Container Count: 4"),
        },
    }


def test_returns_actual_comparison():
    response = client.post("/process/text", json=payload())
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["classification"]["email"]["from"] == "demo@example.com"
    assert result["comparison"]["status"] == "MISMATCH"
    assert result["comparison"]["defect_fields"] == ["container_count"]


def test_missing_documents_require_review():
    data = payload()
    data.pop("si")
    data.pop("bl")
    response = client.post("/process/text", json=data)
    assert response.status_code == 200, response.text
    result = response.json()["comparison"]
    assert result["status"] == "NEEDS_REVIEW"
    assert result["si_document_id"] is None
    assert result["bl_document_id"] is None


def test_noncomparison_email_returns_no_comparison():
    data = payload()
    data["email"]["body"] = "Please explain the invoice charges."
    response = client.post("/process/text", json=data)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["classification"]["category"] == "INVOICE_QUERY"
    assert result["comparison"] is None


def test_rejects_unrelated_attachment():
    data = payload()
    data["bl"]["attachment_path"] = "unrelated.txt"
    response = client.post("/process/text", json=data)
    assert response.status_code == 422
    assert any(
        "email attachments" in error["msg"]
        for error in response.json()["detail"]
    )


def test_rejects_same_attachment_for_both_roles():
    data = payload()
    data["bl"]["attachment_path"] = "si.txt"
    response = client.post("/process/text", json=data)
    assert response.status_code == 422
    assert any(
        "separate SI and BL attachments" in error["msg"]
        for error in response.json()["detail"]
    )
