# Prometeo: verified memory for LLM theorem proving in Lean 4

Code for the MSc thesis "Prometeo desencadenado" (UNAL Manizales): a frozen LLM proposes Lean 4 proofs, the Lean kernel is the only judge, and a library admits only kernel-certified lemmas.

Tantalus, with the 200 Lean refutations of false tasks from the Equational Theories Project: [tantalus/README.md](tantalus/README.md).

## Preregistered confirmatory study

Two primary questions:

- **H1 (memory).** With the same number of attempts, does the model with its certified library solve more tasks than the model without it?
- **H4 (the kernel's filter).** With the same context length and the same origin, are the lemmas the kernel certified worth more as text hints than the proposals it rejected?

The study was registered on OSF on 26 Oct 2026 at 17:47 UTC: <https://osf.io/w4eru> (project: <https://osf.io/vr6wd>).

- SHA-256 of the registered document: `e6a2b5750b1ee1acf6c25bd094ec7c8e206ab02e465e4dd5d6cbd745b8e221fd`
- Git tag: `prereg-v1`

To verify the document:

```bash
git checkout prereg-v1
shasum -a 256 docs/formulacion/prerregistro_confirmatorio_v1_CONGELAR_e6a2b575.md
git checkout main
```

### What the tag contains, and how to check the harness

The tag marks the commit that holds the registered document. **The confirmatory harness and judge are not in that commit.** They ran from an unversioned working copy, and they were added to `main`, byte for byte, in commit `22fad88` on 1 Nov 2026. The registered document identifies them by hash (§5 and §17.17), so they can be checked against it:

- `docs/formulacion/SHA256SUMS_v6` must have SHA-256 `1b69e8ed41bda156793019fde6547cf733777eb35666a3db4b3e4a3c8ebfc98c`.
- `unirl/corpus_confirmatorio.py`, the judge, must start with `c974c63f`.
- The eight files listed in `SHA256SUMS_v6` must match it:

```bash
shasum -a 256 docs/formulacion/SHA256SUMS_v6 unirl/corpus_confirmatorio.py
(cd unirl && grep -v -E 'test_v6.py|fase2.py' ../docs/formulacion/SHA256SUMS_v6 | shasum -a 256 -c -)
(cd tests/unirl && grep test_v6.py ../../docs/formulacion/SHA256SUMS_v6 | shasum -a 256 -c -)
```

Amendment A1 ([docs/formulacion/enmienda_A1_lectura_fase2.md](docs/formulacion/enmienda_A1_lectura_fase2.md)) changed `unirl/fase2.py` before phase 2, so that file no longer matches `SHA256SUMS_v6`. Its current hash is in `docs/formulacion/SHA256SUMS_v6_A1`, and its registered bytes remain in commit `22fad88`:

```bash
(cd unirl && shasum -a 256 -c ../docs/formulacion/SHA256SUMS_v6_A1)
```

`unirl/frontera.py`, which the harness imports, was added in the same commit. Neither `SHA256SUMS_v6` nor the registered document records its hash.

## Status

- **Phase 1 (library construction): finished.** USD 23.98 of a USD 24 cap; 1,808 episodes and 7,772 API calls, all to `claude-haiku-5-5`. It solved 720 of 1,808 episodes (40 %) and completed 26 of 27 families.
- **Phase 2 (the test): pending funding.** 884 tasks from 26 families, with a preregistered cap of USD 260.
- **There are no Phase 2 results yet.**

## Repository map

| Path | Contents |
|---|---|
| `unirl/` | The agent environment, Lean judge and confirmatory harness (`corpus_confirmatorio.py`, `fase1.py`, `fase2.py`, `analisis_v6.py`, …) |
| `tests/` | Automated tests, including the harness tests in `tests/unirl/test_v6.py` |
| `docs/formulacion/` | The registered document, `SHA256SUMS_v6`, and the formulation of the experiments |
| `docs/informes/` | One report per earlier run |
| `docs/ejecuciones_pep/` | Notes on the runs of the performance-estimation (PEP) judge |
| `corpus/`, `certificados/` | Curated Isabelle and stepsize targets and PEP certificates from earlier stages |
| `runs/`, `logs/` | Records and spend ledgers of runs that predate the confirmatory study |
| `resultados/` | Consolidated metrics, statistics and audits of those earlier runs |
| `steprl/` | The PEP judge: SDP verifier, exact rational certificates, evolution with an LLM |
| `isarl/` | The Isabelle judge |
| `didactica/` | The tabular RL agents from the course; it stays here because `unirl` imports it |
| `curso/` | Teaching material for the course (see below) |
| `web/` | A static viewer for `didactica.historia` |
| `MIGRACION.md`, `ESTRUCTURA_OBJETIVO.md` | Old-to-new path table and target layout from the 26 Sep 2026 reorganization |

## Reproducing

- Lean 4.34.1
- Mathlib `d13f23b723b8a846827a245b89c10fc7d3f11612`
- Python 3.11 or later: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
- Harness tests: `python -m pytest tests/unirl/test_v6.py -q`

The API key is read from the environment variable `ANTHROPIC_API_KEY` and never goes in the repository. Running the study also needs the Lean corpus project and the hammer results, which are not in this repository yet; their paths are set with `UNIRL_CORPUS_LEAN` and `UNIRL_MARTILLO`.

## Data and release

All transcripts, libraries and the spend ledger will be published, whatever the result. No GISAID data is included.

## Course agents

`curso/` holds the teaching material for the Numerical Methods course, which predates the thesis. The agents' code is in `didactica/`.

## License

- Code: [Apache-2.0](LICENSE).
- Data, transcripts, corpus and documents: CC BY 4.0, see [LICENSE-DATA.md](LICENSE-DATA.md).
- `curso/` and `didactica/`: MIT ([curso/LICENSE](curso/LICENSE), [didactica/LICENSE](didactica/LICENSE)).

## Citation

See [CITATION.cff](CITATION.cff). Preregistration: <https://osf.io/w4eru>.

## Author and supervision

- **Author:** Carlos Manuel Orrego-Franco ([ORCID 0009-0001-9163-5137](https://orcid.org/0009-0001-9163-5137)), Universidad Nacional de Colombia, Sede Manizales.
- **Thesis supervisors:** Juan Carlos Riaño Rojas (director) and Fabián Fernando Serrano Suárez (co-director).
