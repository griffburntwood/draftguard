import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.extraction import extract_document, extract_text_document


class TestTextExtraction(unittest.TestCase):

    def test_extracts_basic_document(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_001")

        self.assertEqual(result.document_id, "test_doc_001")

        self.assertEqual(
            result.shipper.normalized_value,
            "ABC Trading"
        )

        self.assertEqual(
            result.consignee.normalized_value,
            "XYZ Ltd"
        )

        self.assertEqual(
            result.notify_party.normalized_value,
            "XYZ Ltd"
        )

        self.assertEqual(
            result.port_of_loading.normalized_value,
            "Singapore"
        )

        self.assertEqual(
            result.port_of_discharge.normalized_value,
            "Mersin"
        )

        self.assertEqual(
            result.container_count.normalized_value,
            3
        )

        self.assertEqual(
            result.gross_weight_kg.normalized_value,
            22000
        )

    def test_extracts_alternate_labels(self):
        text = """Shipper Name: ABC Trading
                Consignee Name: XYZ Ltd
                Notify: Notify Company
                POL: Singapore
                POD: Mersin
                No. of Containers: 3
                Gross Weight (kg): 22000"""

        result = extract_text_document(text, "test_doc_002")

        self.assertEqual(
            result.shipper.normalized_value,
            "ABC Trading"
        )
        self.assertEqual(
            result.consignee.normalized_value,
            "XYZ Ltd"
        )
        self.assertEqual(
            result.notify_party.normalized_value,
            "Notify Company"
        )
        self.assertEqual(
            result.port_of_loading.normalized_value,
            "Singapore"
        )
        self.assertEqual(
            result.port_of_discharge.normalized_value,
            "Mersin"
        )
        self.assertEqual(
            result.container_count.normalized_value,
            3
        )
        self.assertEqual(
            result.gross_weight_kg.normalized_value,
            22000
        )

    def test_marks_missing_field_as_missing(self):
        text = """Shipper: ABC Trading
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_003")

        self.assertEqual(
            result.consignee.state.value,
            "missing"
        )
        self.assertIsNone(
            result.consignee.raw_value
        )
        self.assertIsNone(
            result.consignee.normalized_value
        )
        self.assertEqual(
            result.consignee.evidence,
            []
        )

    def test_marks_blank_field_as_missing(self):
        text = """Shipper: ABC Trading
                Consignee:
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_004")

        self.assertEqual(
            result.consignee.state.value,
            "missing"
        )
        self.assertIsNone(
            result.consignee.normalized_value
        )

    def test_preserves_multiline_party_details(self):
        text = """Shipper: ABC Trading Sdn Bhd
                12 Jalan Example
                Kuala Lumpur
                Consignee: XYZ Logistics Ltd
                88 Example Road
                Singapore
                Notify Party: Notify Company
                Port of Loading: Port Klang
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_005")

        self.assertEqual(
            result.shipper.normalized_value,
            "ABC Trading Sdn Bhd\n12 Jalan Example\nKuala Lumpur"
        )

        self.assertEqual(
            result.consignee.normalized_value,
            "XYZ Logistics Ltd\n88 Example Road\nSingapore"
        )

        self.assertEqual(
            result.shipper.raw_value,
            "ABC Trading Sdn Bhd\n12 Jalan Example\nKuala Lumpur"
        )

        self.assertEqual(
            result.shipper.evidence[0].location,
            "TXT: lines 1-3"
        )

        self.assertEqual(
            result.consignee.evidence[0].location,
            "TXT: lines 4-6"
        )

    def test_normalizes_comma_formatted_weight(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22,000 kg"""

        result = extract_text_document(text, "test_doc_006")

        self.assertEqual(
            result.gross_weight_kg.raw_value,
            "22,000 kg"
        )

        self.assertEqual(
            result.gross_weight_kg.normalized_value,
            22000
        )

        self.assertEqual(
            result.gross_weight_kg.state.value,
            "extracted"
        )

    def test_marks_ambiguous_weight_as_ambiguous(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22,000 / 23,000 kg"""

        result = extract_text_document(text, "test_doc_007")

        self.assertEqual(
            result.gross_weight_kg.state.value,
            "ambiguous"
        )

        self.assertEqual(
            result.gross_weight_kg.raw_value,
            "22,000 / 23,000 kg"
        )

        self.assertIsNone(
            result.gross_weight_kg.normalized_value
        )

        self.assertEqual(
            result.gross_weight_kg.evidence[0].location,
            "TXT: line 7"
        )

    def test_marks_ambiguous_container_count_as_ambiguous(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 2 / 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_008")

        self.assertEqual(
            result.container_count.state.value,
            "ambiguous"
        )

        self.assertEqual(
            result.container_count.raw_value,
            "2 / 3"
        )

        self.assertIsNone(
            result.container_count.normalized_value
        )

        self.assertEqual(
            result.container_count.evidence[0].location,
            "TXT: line 6"
        )

    def test_does_not_use_net_weight_as_gross_weight(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Net Weight: 20000 kg"""

        result = extract_text_document(text, "test_doc_009")

        self.assertEqual(
            result.gross_weight_kg.state.value,
            "missing"
        )

        self.assertIsNone(
            result.gross_weight_kg.raw_value
        )

        self.assertIsNone(
            result.gross_weight_kg.normalized_value
        )

        self.assertEqual(
            result.gross_weight_kg.evidence,
            []
        )

    def test_normalizes_decimal_weight(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000.5 kg"""

        result = extract_text_document(text, "test_doc_010")

        self.assertEqual(
            result.gross_weight_kg.raw_value,
            "22000.5 kg"
        )

        self.assertEqual(
            result.gross_weight_kg.normalized_value,
            22000.5
        )

        self.assertEqual(
            result.gross_weight_kg.state.value,
            "extracted"
        )

    def test_preserves_single_line_evidence(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Port of Loading: Singapore
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_011")

        self.assertEqual(
            result.port_of_loading.evidence[0].document_id,
            "test_doc_011"
        )

        self.assertEqual(
            result.port_of_loading.evidence[0].location,
            "TXT: line 4"
        )

        self.assertEqual(
            result.port_of_loading.evidence[0].text,
            "Port of Loading: Singapore"
        )

    def test_extracts_load_port_synonym(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Load Port: Port Klang
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        result = extract_text_document(text, "test_doc_012")

        self.assertEqual(
            result.port_of_loading.normalized_value,
            "Port Klang"
        )

        self.assertEqual(
            result.port_of_loading.state.value,
            "extracted"
        )

    def test_extract_document_reads_txt_file(self):
        text = """Shipper: ABC Trading
                Consignee: XYZ Ltd
                Notify Party: XYZ Ltd
                Load Port: Port Klang
                Port of Discharge: Mersin
                Container Count: 3
                Gross Weight: 22000 kg"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "shipment.txt"
            file_path.write_text(text, encoding="utf-8")

            result = extract_document(file_path, "test_doc_013")

        self.assertEqual(result.document_id, "test_doc_013")
        self.assertEqual(
            result.port_of_loading.normalized_value,
            "Port Klang"
        )
        self.assertEqual(
            result.container_count.normalized_value,
            3
        )
        self.assertEqual(
            result.gross_weight_kg.normalized_value,
            22000
        )

    def test_extract_document_marks_unsupported_formats_as_unreadable(self):
        for extension in [".pdf", ".docx", ".xlsx"]:
            with self.subTest(extension=extension):
                result = extract_document(
                    f"shipment{extension}",
                    f"test_{extension}"
                )

                fields = [
                    result.shipper,
                    result.consignee,
                    result.notify_party,
                    result.port_of_loading,
                    result.port_of_discharge,
                    result.container_count,
                    result.gross_weight_kg,
                ]

                for field in fields:
                    self.assertEqual(
                        field.state.value,
                        "unreadable"
                    )
                    self.assertIsNone(field.raw_value)
                    self.assertIsNone(field.normalized_value)

if __name__ == "__main__":
    unittest.main()
