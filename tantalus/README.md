# Tantalus

[FIRST PARAGRAPH: CARLOS WRITES THIS]

## A defect in our own judge

In an exploratory pilot, our Lean judge rejected correct lemma proposals because of a name clash. In the CC
configuration, a lemma accepted in one attempt was declared again in the Lean file of a later attempt. Lean stopped at
`'<name>' has already been declared` and never checked the new proof. The judge recorded it as a failed proof.

[PILOT NUMBERS: PENDING CARLOS]

The current judge reports this case with its own label, `NOMBRE_YA_DECLARADO`, and says that the proof was not judged
([`unirl/frontera.py`, lines 347 to 350](https://github.com/cmorregof/prometeo/blob/22fad88/unirl/frontera.py#L347-L350)).
That file entered the repository in commit
[`22fad88`](https://github.com/cmorregof/prometeo/commit/22fad88) with the fix already in place.

## 200 refutations in Lean

The folder [`refutaciones_etp/`](refutaciones_etp/) holds 200 false tasks taken from the
[Equational Theories Project](https://github.com/teorth/equational_theories) (ETP), commit `1aec8a7`. Each task says
that one magma law implies another. We refuted all 200 here in Lean 4.34.1 with Mathlib v4.34.1.

| Group | Tasks | How | Axioms |
|---|---:|---|---|
| Finite countermodels | 170 | a table on `Fin n`, closed with `decide` | none |
| Infinite models (family F5) | 30 | models from the ETP, ported from Lean 4.29.1 to Lean 4.34.1 | `propext`, `Classical.choice`, `Quot.sound` in 25; `propext`, `Quot.sound` in 5 |

The 30 F5 tasks are Austin pairs: the first law implies the second in every finite magma, so only an infinite model can
refute them. The port and every change made to it are described in
[`infinitos/LEEME_PORT.md`](refutaciones_etp/infinitos/LEEME_PORT.md). The per-task results are in
[`resumen.csv`](refutaciones_etp/resumen.csv). None of the files uses `native_decide` or `sorry`.

### Check the hashes

`SHA256SUMS` lists the 200 Lean files, the 200 false statements and the ported library. From
`tantalus/refutaciones_etp/`:

```bash
shasum -a 256 -c SHA256SUMS --quiet
```

No output means every file matches.

### Compile

From the repository root, with the Lake files at the root (Lean 4.34.1, Mathlib v4.34.1):

```bash
lake exe cache get
```

```bash
lake build
```

To compile one file and see its axioms:

```bash
lake env lean tantalus/refutaciones_etp/lean/ETP_29_2279.lean
```

It prints `'refuta_29_2279' does not depend on any axioms`. An F5 file needs `lake build` first, because it imports the
ported library:

```bash
lake env lean tantalus/refutaciones_etp/infinitos/lean_f5/ETP_1441_4067.lean
```

It prints `'refuta_1441_4067' depends on axioms: [propext, Classical.choice, Quot.sound]`.

## Errata

The corpus stored these 200 ETP tasks with the label inverted. The stored statement is the negation of the implication.
That negation is true, and it was labeled false. Compiling the refutations exposed the error. We declared it as deviation D1 from the preregistration. See
[`ERRATA_etiqueta_ETP.md`](refutaciones_etp/ERRATA_etiqueta_ETP.md) and
[`DESVIACION_D1_etiqueta_ETP.md`](refutaciones_etp/DESVIACION_D1_etiqueta_ETP.md) (both in Spanish).

## Tests

From the repository root, after `pip install -e ".[dev]"`:

```bash
python -m pytest tests/didactica tests/steprl tests/unirl -m "not isabelle"
```

It collects 427 tests. The 24 tests marked `isabelle` are deselected.

| Where | Pass | Skipped | Deselected |
|---|---:|---:|---:|
| GitHub Actions, Ubuntu, Python 3.12 (run on `main`, 2 Nov 2026) | 375 | 28 | 24 |
| Fresh clone on macOS, Python 3.15, with Isabelle2025 | 378 | 25 | 24 |

On macOS all 25 skipped tests need private files that are not in this repository. Without Isabelle2025, one more test
is skipped.

## Preregistration

- Registration on OSF: <https://osf.io/w4eru>
- OSF project: <https://osf.io/vr6wd>

## License

Code is under [Apache-2.0](../LICENSE). Data, transcripts, corpus and documents are under CC BY 4.0
([LICENSE-DATA.md](../LICENSE-DATA.md)). The files in `refutaciones_etp/testigos_etp/` come from the ETP and keep its
Apache-2.0 license.
