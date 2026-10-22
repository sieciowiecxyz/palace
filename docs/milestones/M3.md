# PR preparation M3 — PASS (2026-10-22)

- M3.1: przeczytano [CONTRIBUTING z bazy](https://github.com/awslabs/palace/blob/29ad351f916e47e005a43730513f155eeb634e3e/CONTRIBUTING.md), [developer notes](https://awslabs.github.io/palace/dev/developer/notes/), [testing](https://awslabs.github.io/palace/dev/developer/testing/), template PR i workflow style (clang-format19).
- Review [#793](https://github.com/awslabs/palace/pull/793): lifecycle reorganizacja odrzucona za zbyt duży diff przy małym zysku. Dlatego tylko finalny uniform solve i osobny pomiar.
- Review [#942](https://github.com/awslabs/palace/pull/942): usunięcie niepowiązanego deferral, restart/durability, changelog/regresje i rzetelny zakres testów. Zastosowano; ograniczenia restartu jawne.
- Review [#882](https://github.com/awslabs/palace/pull/882): zachowanie wariantów solvera, nie sam benchmark. Numeryka bez zmian; zakres CPU/CUDA/MPI jawny.
- M3.2: angielski opis przygotowany lokalnie: `artifacts/upstream-pr/pr-description.md`. Problem, patch, wyniki, failed diagnostics, niewykonane scope i licensing template. Żadnej wiadomości nie wysłano.

Istotne nowe funkcje wymagają według CONTRIBUTING wcześniejszej rozmowy. Ten mały
patch przedstawiamy jako lifecycle improvement; jeśli maintainer uzna inaczej,
użytkownik decyduje o kontakcie. Przyszły mixed-cuDSS wymaga deduplikacji z
[#1058](https://github.com/awslabs/palace/pull/1058). Brak gwarancji akceptacji.
