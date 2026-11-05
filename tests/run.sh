#!/bin/bash
set -u

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root" || exit 1
lake build dosegate >/dev/null || { echo "build failed"; exit 1; }
bin="$root/.lake/build/bin/dosegate"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

pass=0
fail=0

for request in tests/cases/*.request.json; do
    name="$(basename "$request" .request.json)"
    expected="tests/cases/$name.expected.json"
    words="$root/tests/cases/$name.words"
    extra=""
    [ -f "$words" ] && extra="--extra-words $words"
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
    "$bin" render < "$request" > "$out/actual.json"
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

python3 -c 'import json; m = [{"resourceType": "MedicationRequest", "id": "x%d" % i, "status": "active", "intent": "order", "medicationCodeableConcept": {"text": "aspirin"}} for i in range(5001)]; print(json.dumps({"medicationRequests": m, "output": "Take {{drug:x1}}."}))' > "$out/many_orders.json"
echo '{"status": "error", "message": "the request has more than 5000 MedicationRequests"}' > "$out/many_orders.expected.json"
"$bin" render < "$out/many_orders.json" > "$out/actual.json"
code=$?
if python3 tests/check.py case "$out/actual.json" "$code" "$out/many_orders.expected.json"; then
    pass=$((pass + 1))
else
    echo "FAIL order count limit"
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

echo "passed: $pass, failed: $fail"
[ "$fail" -eq 0 ]
