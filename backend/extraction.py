"""Label-based shipment extraction with conservative uncertainty handling."""
import math
import re
import unicodedata
from decimal import Decimal, InvalidOperation

from .models import ExtractedField, ExtractionState, ShipmentField, ShipmentRecord, SourceEvidence

LABELS = {
    'shipper': ['Shipper', 'Shipper Name', 'Shipper/Exporter', 'Shipper (Principal or Seller)', 'Exporter'],
    'consignee': ['Consignee', 'Consignee Name', 'Consignee (Non-Negotiable)', 'To the Order of'],
    'notify_party': ['Notify', 'Notify Party', 'Notify Party/Intermediate Consignee'],
    'port_of_loading': ['Port of Loading', 'POL', 'Port of Loading (POL)', 'Load Port'],
    'port_of_discharge': ['Port of Discharge', 'POD', 'Port of Discharge (POD)', 'Discharge Port'],
    'container_count': ['Container Count', 'No. of Containers', 'Total Containers', 'No. of Containers or Packages'],
    'gross_weight_kg': ['Gross Weight', 'Gross Weight (kg)', 'Gross Wt (kgs)', 'Gross Weight毛重(KGS)', 'TOTAL GROSS WEIGHT', 'TOTAL Gross Weight (KG)', 'TOTAL Gross Wt (kgs)', 'TOTAL Gross Weight毛重(KGS)', 'TOTAL Gross Weightnn(KGS)'],
}
PARTIES = {'shipper', 'consignee', 'notify_party'}
PLACEHOLDERS = {'', '-', '--', 'n/a', 'na', 'none', 'null', 'unknown', 'not available', 'tbd'}


def label_key(text):
    text = re.sub(r'\([^)]*[\u3400-\u9fff][^)]*\)', '', text)
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text)).strip().casefold()


LABEL_MAP = {label_key(label): field for field, labels in LABELS.items() for label in labels}


def split_label(line):
    parts = re.split(r'[:：]', line.strip(), maxsplit=1)
    return (LABEL_MAP.get(label_key(parts[0])), parts[1].strip()) if len(parts) == 2 else (None, '')


def normalize_number(field, raw):
    if field == 'container_count':
        if re.fullmatch(r'[0-9]+', raw):
            return int(raw)
        # Only complete equipment expressions are accepted; never take an arbitrary first digit.
        match = re.fullmatch(r"([0-9]+)\s*[x×]\s*(?:20|40|45)\s*['’′]?\s*(?:HC|HQ|GP|DC|FCL)", raw, re.I)
        if match:
            return int(match.group(1))
        raise ValueError('Ambiguous container count')
    match = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?|[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?)\s*(kg|kgs|kilograms?|mt|mts|tonnes?|t)?', raw, re.I)
    if not match:
        raise ValueError('Ambiguous weight or unit')
    value = Decimal(match.group(1).replace(',', ''))
    if (match.group(2) or '').lower() in {'mt', 'mts', 'tonne', 'tonnes', 't'}:
        value *= 1000
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError('Invalid weight')
    return int(value) if value == value.to_integral_value() else number


def empty_record(document_id, state=ExtractionState.UNREADABLE):
    return ShipmentRecord(document_id=document_id, **{
        field.value: ExtractedField(raw_value=None, normalized_value=None, state=state, evidence=[])
        for field in ShipmentField
    })


def extract_text_document(text: str, document_id: str, *, locations: list[str] | None = None) -> ShipmentRecord:
    lines = text.splitlines()
    occurrences = {name: [] for name in LABELS}
    for index, line in enumerate(lines):
        field, value = split_label(line)
        if field:
            occurrences[field].append((index, value))
    extracted = {}
    for field, found in occurrences.items():
        if not found:
            extracted[field] = ExtractedField(raw_value=None, normalized_value=None, state=ExtractionState.MISSING, evidence=[])
            continue
        sources = []
        raw_values = []
        for start, value in found:
            end = start
            values = [value] if value else []
            if field in PARTIES:
                for index in range(start + 1, len(lines)):
                    next_line = lines[index].strip()
                    if not next_line or split_label(next_line)[0]:
                        break
                    # Other document metadata is a boundary too; PO Box address lines are not.
                    if ':' in next_line and not re.match(r'(?i)^(?:p\.?\s*o\.?\s*box|tel|fax|phone)\b', next_line):
                        break
                    values.append(next_line)
                    end = index
            raw = '\n'.join(values).strip()
            raw_values.append(raw)
            if locations:
                location = '; '.join(dict.fromkeys(locations[start:end + 1]))
            else:
                location = f'TXT: line {start + 1}' if start == end else f'TXT: lines {start + 1}-{end + 1}'
            sources.append(SourceEvidence(document_id=document_id, location=location, text='\n'.join(s.strip() for s in lines[start:end + 1])))
        raw = '\n'.join(raw_values)
        state = ExtractionState.EXTRACTED
        normalized = raw
        if '[formula unavailable]' in raw:
            state, normalized = ExtractionState.UNREADABLE, None
        elif len(found) > 1:
            state, normalized = ExtractionState.AMBIGUOUS, None
        elif label_key(raw) in PLACEHOLDERS or re.fullmatch(r'[_\s?]+', raw):
            state, normalized = ExtractionState.MISSING, None
        elif field in {'container_count', 'gross_weight_kg'}:
            try:
                normalized = normalize_number(field, raw)
            except (ValueError, InvalidOperation, OverflowError):
                state, normalized = ExtractionState.AMBIGUOUS, None
        extracted[field] = ExtractedField(raw_value=raw or None, normalized_value=normalized, state=state, evidence=sources)
    return ShipmentRecord(document_id=document_id, **extracted)
