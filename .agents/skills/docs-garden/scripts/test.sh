#!/bin/sh
set -eu
base=$(mktemp -d)
trap 'rm -rf "$base"' EXIT HUP INT TERM
mkdir -p "$base/.agents/skills/docs-garden/scripts" "$base/docs/milestones"
cp "$(dirname "$0")/check.sh" "$base/.agents/skills/docs-garden/scripts/"
check="$base/.agents/skills/docs-garden/scripts/check.sh"
printf '# Zasady\n' > "$base/AGENTS.md"
cat > "$base/docs/INDEX.md" <<'EOF'
# Indeks
- [Notatki](notes.md)
  - Czytaj gdy: edycja.
  - Opis: fakty.
EOF
printf '# Fakty\n' > "$base/docs/notes.md"
cat > "$base/PLAN.md" <<'EOF'
Mode: template
Active: none
EOF
ok() { sh "$check" >/dev/null || { echo "TEST: oczekiwany sukces, etap=$stage" >&2; cat "$base/docs/INDEX.md" >&2; exit 1; }; }
bad() { if sh "$check" >/dev/null 2>&1; then echo 'TEST: oczekiwany błąd' >&2; exit 1; fi; }

stage=template
ok                                # zwykły projekt, bez MILESTONES i Cargo
printf '# Brak\n' > "$base/docs/extra.md"
bad                               # brak indeksowania
rm "$base/docs/extra.md"
sed 's/  - Opis: fakty./  - Opis:/' "$base/docs/INDEX.md" > "$base/docs/new.md"
mv "$base/docs/new.md" "$base/docs/INDEX.md"
bad                               # pusty opis
cat > "$base/docs/INDEX.md" <<'EOF'
# Indeks
- [Notatki](notes.md)
  - Czytaj gdy: edycja.
  - Opis: fakty.
EOF
cat > "$base/PLAN.md" <<'EOF'
Mode: goal
Active: M0
## Milestones
- [ ] M0 - Pierwszy
- [ ] M1 - Drugi
EOF
cat > "$base/MILESTONES.md" <<'EOF'
# Kontrakt
## M0 - Pierwszy
- M0.1: Działa
## M1 - Drugi
- M1.1: Test
EOF
bad                               # brak checkpointu
printf '# M0\n' > "$base/docs/milestones/M0.md"
cat >> "$base/docs/INDEX.md" <<'EOF'
- [M0](milestones/M0.md)
  - Czytaj gdy: M0.
  - Opis: dowody.
EOF
stage=goal
ok                                # goal poprawny
cat >> "$base/docs/INDEX.md" <<'EOF'
- [Duplikat](./notes.md)
  - Czytaj gdy: ponowna edycja.
  - Opis: duplikat.
EOF
bad                               # duplikat
sed '/^- \[Duplikat\]/,$d' "$base/docs/INDEX.md" > "$base/docs/new.md"
mv "$base/docs/new.md" "$base/docs/INDEX.md"
sed 's/M0.1:/M0.2:/' "$base/MILESTONES.md" > "$base/MILESTONES.md.tmp"
mv "$base/MILESTONES.md.tmp" "$base/MILESTONES.md"
bad                               # błędna numeracja
sed 's/M0.2:/M0.1:/' "$base/MILESTONES.md" > "$base/MILESTONES.md.tmp"
mv "$base/MILESTONES.md.tmp" "$base/MILESTONES.md"
cat > "$base/PLAN.md" <<'EOF'
Mode: goal
Active: M1
## Milestones
- [ ] M0 - Pierwszy
- [x] M1 - Drugi
EOF
bad                               # pominięty milestone
printf 'OK: 8 testów shell\n'
