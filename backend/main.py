from fastapi import FastAPI

app = FastAPI(
    title="DraftGuard API",
    description="Shipping document review and revision tracking.",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "draftguard",
    }


@app.get("/demo/comparison")
def demo_comparison():
    """Static example for frontend development, not actual processing."""

    examples = [
        ("shipper", "ABC Trading", "ABC Trading"),
        ("consignee", "XYZ Ltd", "XYZ Ltd"),
        ("notify_party", "XYZ Ltd", "XYZ Ltd"),
        ("port_of_loading", "Singapore", "Singapore"),
        ("port_of_discharge", "Mersin", "Mersin"),
        ("container_count", 3, 4),
        ("gross_weight_kg", 22000, 22000),
    ]

    def extracted(value, document_id, field_name):
        return {
            "raw_value": str(value),
            "normalized_value": value,
            "state": "extracted",
            "evidence": [{
                "document_id": document_id,
                "location": f"Synthetic example: {field_name}",
                "text": f"{field_name}: {value}",
            }],
        }

    field_results = []
    for name, si_value, bl_value in examples:
        matches = si_value == bl_value
        field_results.append({
            "field": name,
            "si": extracted(si_value, "demo_si_v1", name),
            "bl": extracted(bl_value, "demo_bl_v1", name),
            "outcome": "MATCH" if matches else "MISMATCH",
            "explanation": (
                "Values match."
                if matches
                else "SI specifies 3 containers; draft BL specifies 4."
            ),
        })

    return {
        "is_demo": True,
        "notice": "Synthetic example. No documents were processed.",
        "comparison_id": "demo_comparison_001",
        "email_id": "demo_email_001",
        "si_document_id": "demo_si_v1",
        "bl_document_id": "demo_bl_v1",
        "status": "MISMATCH",
        "field_results": field_results,
        "defect_fields": ["container_count"],
        "review_reasons": [],
    }
