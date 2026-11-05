from raw import *
import subprocess, json
cases = [
 ("top_array", "[1,2]"),
 ("top_string", '"hi"'),
 ("top_null", "null"),
 ("empty_stdin", ""),
 ("output_number", '{"bundle": {"entry": []}, "output": 5}'),
 ("output_null", '{"bundle": {"entry": []}, "output": null}'),
 ("bundle_string", '{"bundle": "x", "output": "Take {{drug:m1}}."}'),
 ("medreqs_not_array", '{"medicationRequests": "x", "output": "Take {{drug:m1}}."}'),
 ("allow_not_array", '{"bundle": {"entry": []}, "output": "ok", "allow": "911"}'),
 ("allow_nonstring", '{"bundle": {"entry": []}, "output": "ok", "allow": [1, null]}'),
 ("nested_bundle_entry_not_obj", '{"bundle": {"entry": [1, "x", null]}, "output": "ok"}'),
 ("id_number", '{"bundle": {"entry": [{"resource": {"resourceType": "MedicationRequest", "id": 5, "status": "active"}}]}, "output": "ok"}'),
 ("empty_output", '{"bundle": {"entry": []}, "output": ""}'),
 ("output_braces_unicode_escape", '{"bundle": {"entry": []}, "output": "\\u007b\\u007bdrug:m1\\u007d\\u007d"}'),
 ("output_NUL", '{"bundle": {"entry": []}, "output": "a\\u0000b"}'),
 ("output_surrogate_pair", '{"bundle": {"entry": []}, "output": "\\ud83d\\ude00 ok"}'),
 ("output_lone_surrogate", '{"bundle": {"entry": []}, "output": "\\ud83d ok"}'),
 ("bundle_entry_bad_id_dup_drop", '{"bundle": {"entry": [{"resource": {"resourceType": "MedicationRequest", "id": "m1", "status": "active", "dosageInstruction": [{"doseAndRate": [{"doseQuantity": {"value": 5, "code": "mg"}}]}]}}, {"resource": {"resourceType": "medicationrequest", "id": "m1", "status": "stopped"}}]}, "output": "Take {{drug:m1}} {{dose:m1}}."}'),
]
for name, body in cases:
    rc, out, err, t = run(body)
    print(f"[{name}] rc={rc} {out[:200]} {err[:120]}")
