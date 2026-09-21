"""Plain-text document extraction for DraftGuard."""

import math

from backend.models import (
    ExtractedField,
    ExtractionState,
    ShipmentRecord,
    SourceEvidence,
)


def extract_text_document(text: str, document_id: str) -> ShipmentRecord:
    """Extract the seven required shipment fields from plain text."""

    lines = text.splitlines()

    labels = {
        "shipper": [
            "Shipper:",
            "Shipper Name:",
        ],
        "consignee": [
            "Consignee:",
            "Consignee Name:",
        ],
        "notify_party": [
            "Notify Party:",
            "Notify:",
        ],
        "port_of_loading": [
            "Port of Loading:",
            "POL:",
        ],
        "port_of_discharge": [
            "Port of Discharge:",
            "POD:",
        ],
        "container_count": [
            "Container Count:",
            "No. of Containers:",
        ],
        "gross_weight_kg": [
            "Gross Weight:",
            "Gross Weight (kg):",
        ],
    }

    party_fields = {
        "shipper",
        "consignee",
        "notify_party",
    }

    extracted = {}

    for field_name, possible_labels in labels.items():
        occurrences = [
            (number, line)
            for number, line in enumerate(lines, start=1)
            if any(
                line.strip().lower().startswith(label.lower())
                for label in possible_labels
            )
        ]
        if len(occurrences) > 1:
            extracted[field_name] = ExtractedField(
                raw_value="\n".join(line.strip() for _, line in occurrences),
                normalized_value=None,
                state=ExtractionState.AMBIGUOUS,
                evidence=[
                    SourceEvidence(
                        document_id=document_id,
                        location=f"TXT: line {number}",
                        text=line,
                    )
                    for number, line in occurrences
                ],
            )
            continue

        for line_number, line in enumerate(lines, start=1):
            stripped_line = line.strip()

            matched_label = next(
                (
                    label
                    for label in possible_labels
                    if stripped_line.lower().startswith(label.lower())
                ),
                None,
            )

            if matched_label is not None:
                raw_value = stripped_line[len(matched_label):].strip()

                end_line_number = line_number

                if field_name in party_fields and raw_value:
                    value_lines = [raw_value]

                    for next_index in range(line_number, len(lines)):
                        next_line = lines[next_index].strip()

                        if not next_line:
                            break

                        is_new_field = any(
                            next_line.lower().startswith(label.lower())
                            for field_labels in labels.values()
                            for label in field_labels
                        )

                        if is_new_field:
                            break

                        value_lines.append(next_line)
                        end_line_number = next_index + 1

                    raw_value = "\n".join(value_lines)

                if not raw_value:
                    extracted[field_name] = ExtractedField(
                        raw_value=None,
                        normalized_value=None,
                        state=ExtractionState.MISSING,
                        evidence=[
                            SourceEvidence(
                                document_id=document_id,
                                location=(
                                    f"TXT: line {line_number}"
                                    if end_line_number == line_number
                                    else f"TXT: lines {line_number}-{end_line_number}"
                                ),
                                text=line,
                            )
                        ],
                    )
                    break

                normalized_value = raw_value

                if field_name == "container_count":
                    try:
                        normalized_value = int(raw_value)
                        if normalized_value < 0:
                            raise ValueError("Negative container count")
                    except ValueError:
                        extracted[field_name] = ExtractedField(
                            raw_value=raw_value,
                            normalized_value=None,
                            state=ExtractionState.AMBIGUOUS,
                            evidence=[
                                SourceEvidence(
                                    document_id=document_id,
                                    location=f"TXT: line {line_number}",
                                    text=line,
                                )
                            ],
                        )
                        break

                elif field_name == "gross_weight_kg":
                    weight_text = (
                        raw_value.lower()
                        .replace("kg", "")
                        .replace(",", "")
                        .strip()
                    )

                    try:
                        normalized_value = float(weight_text)
                        if not math.isfinite(normalized_value) or normalized_value < 0:
                            raise ValueError("Invalid gross weight")

                        if normalized_value.is_integer():
                            normalized_value = int(normalized_value)

                    except ValueError:
                        extracted[field_name] = ExtractedField(
                            raw_value=raw_value,
                            normalized_value=None,
                            state=ExtractionState.AMBIGUOUS,
                            evidence=[
                                SourceEvidence(
                                    document_id=document_id,
                                    location=f"TXT: line {line_number}",
                                    text=line,
                                )
                            ],
                        )
                        break

                extracted[field_name] = ExtractedField(
                    raw_value=raw_value,
                    normalized_value=normalized_value,
                    state=ExtractionState.EXTRACTED,
                    evidence=[
                        SourceEvidence(
                            document_id=document_id,
                            location=(
                                f"TXT: line {line_number}"
                                if end_line_number == line_number
                                else f"TXT: lines {line_number}-{end_line_number}"
                            ),
                            text="\n".join(
                                source_line.strip()
                                for source_line in lines[line_number - 1:end_line_number]
                            ),
                        )
                    ],
                )

                break

    for field_name in labels:
        if field_name not in extracted:
            extracted[field_name] = ExtractedField(
                raw_value=None,
                normalized_value=None,
                state=ExtractionState.MISSING,
                evidence=[],
            )

    return ShipmentRecord(
        document_id=document_id,
        shipper=extracted["shipper"],
        consignee=extracted["consignee"],
        notify_party=extracted["notify_party"],
        port_of_loading=extracted["port_of_loading"],
        port_of_discharge=extracted["port_of_discharge"],
        container_count=extracted["container_count"],
        gross_weight_kg=extracted["gross_weight_kg"],
    )
