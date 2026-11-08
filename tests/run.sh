#!/bin/bash
set -u

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
lake build dosegate >/dev/null || { echo "build failed"; exit 1; }
bin="$root/.lake/build/bin/dosegate"
out="$(mktemp -d "${TMPDIR:-/tmp}/dosegate-tests.XXXXXX")"
trap 'rm -rf "$out"' EXIT

pass=0
fail=0

for request in tests/cases/*.request.json; do
    name="$(basename "$request" .request.json)"
    expected="tests/cases/$name.expected.json"
    words="$root/tests/cases/$name.words"
    extra=""
    [ -f "$words" ] && extra="--extra-words $words"
    flags="$root/tests/cases/$name.flags"
    [ -f "$flags" ] && extra="$extra $(cat "$flags")"
    python3 tests/check.py merge "$request" tests/bundle.json > "$out/in.json"
    "$bin" render $extra < "$out/in.json" > "$out/actual.json"
    code=$?
    if python3 tests/check.py case "$out/actual.json" "$code" "$expected"; then
        pass=$((pass + 1))
    else
        echo "FAIL render $name"
        fail=$((fail + 1))
    fi
done

for request in tests/raw/*.request.json; do
    name="$(basename "$request" .request.json)"
    expected="tests/raw/$name.expected.json"
    flags="$root/tests/raw/$name.flags"
    extra=""
    [ -f "$flags" ] && extra="$(cat "$flags")"
    "$bin" render $extra < "$request" > "$out/actual.json"
    code=$?
    if python3 tests/check.py case "$out/actual.json" "$code" "$expected"; then
        pass=$((pass + 1))
    else
        echo "FAIL raw $name"
        fail=$((fail + 1))
    fi
done

python3 -c 'import json; print(json.dumps({"medicationRequests": [], "output": "a " * 40000}))' > "$out/long_output.json"
echo '{"status": "error", "message": "the output is longer than 65536 characters"}' > "$out/long_output.expected.json"
"$bin" render < "$out/long_output.json" > "$out/actual.json"
code=$?
if python3 tests/check.py case "$out/actual.json" "$code" "$out/long_output.expected.json"; then
    pass=$((pass + 1))
else
    echo "FAIL output length limit"
    fail=$((fail + 1))
fi

python3 -c 'import json; m = [{"resourceType": "MedicationRequest", "id": "x%d" % i, "status": "active", "intent": "order", "medicationCodeableConcept": {"text": "aspirin"}, "subject": {"reference": "Patient/pat1"}} for i in range(5001)]; print(json.dumps({"medicationRequests": m, "output": "Take {{drug:x1}}."}))' > "$out/many_orders.json"
echo '{"status": "error", "message": "the request has more than 5000 MedicationRequests"}' > "$out/many_orders.expected.json"
"$bin" render < "$out/many_orders.json" > "$out/actual.json"
code=$?
if python3 tests/check.py case "$out/actual.json" "$code" "$out/many_orders.expected.json"; then
    pass=$((pass + 1))
else
    echo "FAIL order count limit"
    fail=$((fail + 1))
fi

python3 -c 'import json; print(json.dumps({"output": "a" * 2000000}))' > "$out/big_request.json"
echo '{"status": "error", "message": "the request is larger than 2000000 bytes"}' > "$out/big_request.expected.json"
"$bin" render < "$out/big_request.json" > "$out/actual.json"
code=$?
if python3 tests/check.py case "$out/actual.json" "$code" "$out/big_request.expected.json"; then
    pass=$((pass + 1))
else
    echo "FAIL request size limit"
    fail=$((fail + 1))
fi

python3 -c 'import json; print(json.dumps({"medicationRequests": [], "output": "{{drug:m1}} " * 401}))' > "$out/slots_401.json"
echo '{"status": "error", "message": "the output has more than 400 slots"}' > "$out/slots_401.expected.json"
"$bin" render < "$out/slots_401.json" > "$out/actual.json"
code=$?
if python3 tests/check.py case "$out/actual.json" "$code" "$out/slots_401.expected.json"; then
    pass=$((pass + 1))
else
    echo "FAIL slot count limit"
    fail=$((fail + 1))
fi

python3 - "$out/slots_400.json" "$out/slots_400.expected.json" <<'EOF'
import json, sys
names = [line.strip() for line in open("tests/words/slot_names.txt") if line.strip()]
route = {"coding": [{"system": "http://snomed.info/sct", "code": "26643006", "display": "Oral route"}]}
orders = []
for n in names:
    orders.append({"resourceType": "MedicationRequest", "id": "o" + n, "status": "active", "intent": "order",
                   "medicationCodeableConcept": {"text": n}, "subject": {"reference": "Patient/pat1"},
                   "dosageInstruction": [{"timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                                          "route": route,
                                          "doseAndRate": [{"doseQuantity": {"value": 81, "unit": "mg",
                                                           "system": "http://unitsofmeasure.org", "code": "mg"}}]}]})
output = " ".join("Take {{drug:o%s}} {{dose:o%s}} {{route:o%s}} {{frequency:o%s}}." % (n, n, n, n) for n in names)
text = " ".join("Take %s 81 mg by mouth once a day." % n for n in names)
json.dump({"medicationRequests": orders, "output": output}, open(sys.argv[1], "w"))
json.dump({"status": "ok", "text": text}, open(sys.argv[2], "w"))
EOF
"$bin" render < "$out/slots_400.json" > "$out/actual.json"
code=$?
if python3 tests/check.py case "$out/actual.json" "$code" "$out/slots_400.expected.json"; then
    pass=$((pass + 1))
else
    echo "FAIL 400 slots accepted"
    fail=$((fail + 1))
fi

if "$bin" render --extra-words tests/words/uppercase.words < /dev/null > /dev/null 2>&1; then
    echo "FAIL uppercase extra-words file was accepted"
    fail=$((fail + 1))
else
    pass=$((pass + 1))
fi

"$bin" serve < tests/serve/session.in.jsonl > "$out/serve.jsonl"
if python3 tests/check.py lines "$out/serve.jsonl" tests/serve/session.expected.jsonl; then
    pass=$((pass + 1))
else
    echo "FAIL serve session"
    fail=$((fail + 1))
fi

for request in tests/fallback/*.request.json; do
    name="$(basename "$request" .request.json)"
    expected="tests/fallback/$name.expected.json"
    "$bin" fallback < "$request" > "$out/actual.json"
    code=$?
    if python3 tests/check.py case "$out/actual.json" "$code" "$expected"; then
        pass=$((pass + 1))
    else
        echo "FAIL fallback $name"
        fail=$((fail + 1))
    fi
done

echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
