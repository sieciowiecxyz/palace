#!/bin/sh
# Bez bibliotek: sh, awk, find, wc.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/../../../.." && pwd)"
[ -f AGENTS.md ] && [ -f docs/INDEX.md ] || {
  echo 'BŁĄD: brak AGENTS.md lub docs/INDEX.md' >&2
  exit 1
}

# Każdy dokument w docs/ ma dokładnie jeden wpis z dwiema etykietami.
list=$(mktemp)
trap 'rm -f "$list"' EXIT HUP INT TERM
find docs -type f \( -name '*.md' -o -name '*.MD' \) | LC_ALL=C sort > "$list"
awk '
function fail(msg) { print "BŁĄD INDEX: " msg > "/dev/stderr"; bad = 1 }
function finish() { if (entry && (!when || !description)) fail("brak Czytaj gdy / Opis przy " entry) }
FILENAME == "docs/INDEX.md" {
  line = $0; n = FNR
  if (substr(line, 1, 3) == "~~~" || substr(line, 1, 3) == sprintf("%c%c%c", 96, 96, 96)) { if (!fence) finish(); fence = !fence; next }
  if (fence) next
  if (line ~ /^- /) {
    finish(); entry = ""; when = description = 0
    if (line !~ /^- \[[^]]+\]\([^)]+\.md\)$/) { fail("niepoprawny link, linia " n); next }
    path = line; sub(/^.*\]\(/, "", path); sub(/\)$/, "", path)
    if (path ~ /(^\/|^\.\.\/|\/\.\.\/|\/\.\/?|:|#|\?|%|\\)/) { fail("niedozwolona ścieżka: " path); next }
    sub(/^\.\//, "", path)
    entry = "docs/" path
    if (++links[entry] > 1) fail("duplikat: " entry)
  } else if (line ~ /^  - /) {
    if (!entry) { fail("pole bez linku, linia " n); next }
    if (line ~ /^  - Czytaj gdy: [^ ]/ && !when && !description) when = 1
    else if (line ~ /^  - Opis: [^ ]/ && when && !description) description = 1
    else fail("niepoprawne lub powtórzone pole, linia " n)
  } else if (line !~ /^[[:space:]]*$/) { finish(); entry = "" }
  next
}
{
  if ($0 == "docs/INDEX.md") next
  seen[$0] = 1
  if (!links[$0]) fail("brak wpisu dla " $0)
}
END {
  finish()
  for (path in links) if (!seen[path]) fail("brak pliku " path)
  if (bad) exit 1
}
' docs/INDEX.md "$list"

# Blokuj pominięte milestones, rozjazd kontraktu i błędne identyfikatory.
if [ -f PLAN.md ]; then
  contract=MILESTONES.md
  [ -f "$contract" ] || contract=/dev/null
  awk '
function fail(msg) { print "BŁĄD PLAN: " msg > "/dev/stderr"; bad = 1 }
FILENAME == "PLAN.md" {
  if ($0 ~ /^Mode: /) { mode_count++; mode = substr($0,7) }
  if ($0 ~ /^Active: /) { active_count++; active = substr($0,9) }
  if ($0 == "## Milestones") { in_list = 1; next }
  if ($0 ~ /^## /) in_list = 0
  if (in_list && $0 ~ /^- \[[ x]\] /) {
    value = $0; sub(/^- \[[ x]\] /, "", value); split(value, parts, " ")
    id = parts[1]; n++; ids[n] = id
    if (id != "M" (n - 1)) fail("kolejność milestones: " id)
    done = ($0 ~ /^- \[x\] /)
    if (!done && !first) first = id
    if (done && first) fail("ukończono kolejny milestone przed poprzednim")
    if (done && id ~ /^M[0-9]+$/) required[id] = 1
  }
  next
}
FILENAME == "MILESTONES.md" {
  if ($0 ~ /^## M[0-9]+ - /) {
    value = $0; sub(/^## /, "", value); split(value, parts, " ")
    current = parts[1]; contract_n++
    if (current != ids[contract_n]) fail("PLAN i MILESTONES są niespójne")
    number = 0
  } else if ($0 ~ /^- M[0-9]+\.[0-9]+:/) {
    value = $0; sub(/^- /, "", value); sub(/:.*/, "", value)
    number++
    if (value != current "." number) fail("zła numeracja kryterium: " value)
  } else if ($0 ~ /^- \[[ x]\] /) fail("checkboxy tylko w PLAN")
}
END {
  if (mode_count != 1 || active_count != 1) fail("Mode / Active musi wystąpić raz")
  if (mode == "template" || mode == "normal") {
    if (active != "none") fail("nieaktywny tryb wymaga Active: none")
  } else if (mode == "goal") {
    if (!n) fail("brak milestones")
    if (contract_n != n) fail("PLAN i MILESTONES mają różne etapy")
    expected = first ? first : "none"
    if (active != expected) fail("Active powinno wynosić " expected)
    if (active != "none" && active ~ /^M[0-9]+$/) required[active] = 1
    for (id in required) if (system("test -f docs/milestones/" id ".md") != 0) fail("brak checkpointu " id)
  } else fail("nieznany Mode: " mode)
  if (bad) exit 1
}
' PLAN.md "$contract"
fi

# Szacunek polskich dokumentów: ~1 token na 3,2 bajta UTF-8 (nie tokenizer).
files='AGENTS.md ARCHITECTURE.md BOOTSTRAP.md MILESTONES.md PLAN.md README.md'
for f in $files; do
  [ -f "$f" ] || continue
  bytes=$(wc -c < "$f")
  est=$(( (bytes * 10 + 31) / 32 ))
  printf '%5s ~tok  %s\n' "$est" "$f"
  if [ "$f" = AGENTS.md ] && [ "$est" -gt 500 ]; then echo 'UWAGA: AGENTS.md > ~500 tokenów' >&2; fi
done
find docs -type f \( -name '*.md' -o -name '*.MD' \) | LC_ALL=C sort | while IFS= read -r f; do
  bytes=$(wc -c < "$f")
  est=$(( (bytes * 10 + 31) / 32 ))
  printf '%5s ~tok  %s\n' "$est" "$f"
done
printf 'OK: indeks i etapy sprawdzone. Liczby ~tok są jedynie szacunkiem.\n'
