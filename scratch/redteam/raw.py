import subprocess, json, time
BIN = "/Volumes/T7/Dosing_formal_verification/.lake/build/bin/dosegate"
ROUTE_ORAL = '"route": {"coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]}'
FREQ_DAILY = '"timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}'

def dose_block(val, code="mg"):
    return '"doseAndRate": [{"doseQuantity": {"value": %s, "code": "%s"}}]' % (val, code)

def mr(id_, dosage_fields, status='"active"', extra=""):
    return ('{"resource": {"resourceType": "MedicationRequest", "id": "%s", "status": %s, %s'
            '"medicationCodeableConcept": {"text": "metformin"}, "dosageInstruction": [{%s}]}}') % (id_, status, extra, dosage_fields)

def request(entries, output):
    return '{"bundle": {"resourceType": "Bundle", "entry": [%s]}, "output": %s}' % (", ".join(entries), json.dumps(output))

def run(req_json, timeout=60):
    t = time.time()
    try:
        p = subprocess.run([BIN, "render"], input=req_json.encode("utf-8"), capture_output=True, timeout=timeout)
        return p.returncode, p.stdout.decode("utf-8", "replace").strip()[:400], p.stderr.decode("utf-8", "replace")[:200], round(time.time() - t, 2)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", "", timeout
