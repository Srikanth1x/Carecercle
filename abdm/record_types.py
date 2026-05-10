PRESCRIPTION = "Prescription"
DIAGNOSTIC_REPORT = "DiagnosticReport"
WELLNESS_RECORD = "WellnessRecord"
DISCHARGE_SUMMARY = "DischargeSummary"
IMMUNIZATION_RECORD = "ImmunizationRecord"

VALID_TYPES = {PRESCRIPTION, DIAGNOSTIC_REPORT, WELLNESS_RECORD, DISCHARGE_SUMMARY, IMMUNIZATION_RECORD}

def validate(record_type: str) -> str:
    if record_type not in VALID_TYPES:
        raise ValueError(f"Invalid ABDM record type: {record_type}")
    return record_type
