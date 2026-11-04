# Re-judging the pilot after the name-clash fix

This page summarizes how we re-judged the lemmas that the pilot rejected because of the name-clash defect described in
[README.md](README.md#a-defect-in-our-own-judge). The run took place on 25 Oct 2026 and made no API calls.

## The runs

The pilot had four runs of `claude-opus-5-5` in the CC configuration (with a persistent notebook of accepted lemmas),
on 24 Oct 2026. Each run had 10 episodes on one magma law.

| Law | Lemmas submitted | Accepted | Rejected | Rejected by a name clash | Rejected for other reasons |
|---|---:|---:|---:|---:|---:|
| E13102 | 100 | 33 | 67 | 67 | 0 |
| E1486_12 | 86 | 26 | 60 | 60 | 0 |
| E20911 | 94 | 32 | 62 | 61 | 1 |
| E23357 | 53 | 19 | 34 | 30 | 4 |
| **Total** | **333** | **110** | **223** | **218** | **5** |

A rejection counts as a name clash when Lean reported `has already been declared`.

## Two judges

The table above and the tables under [Results](#results) come from two different judges.

- **The pilot** was judged by `unirl/frontera.py` as it stood before the fix. The run metadata (`meta.json`, field
  `codigo`) recorded only a 16-character fingerprint of four harness files (`frontera.py`, `juez_lean.py`, `loop.py`,
  `gasto.py`): `4dde23ec5862dde9`, the same in the four runs. The runs did not record the SHA-256 of `frontera.py`
  alone. A copy of `frontera.py` saved before the fix, with SHA-256
  `3ef64496f1a5a4d458bbdc9b4fe87b52eb1de5512e2bff16133cd1b3fe9b55bf`, reproduces that fingerprint together with the
  current versions of the other three files.
- **The re-judging** used the patched file, SHA-256
  `59b983ee829aea8da8d237fabe4d0e8c61a7fd49be2880b5683513f61e6d69fd`. The fix was made on 24 Oct 2026 in a working
  copy where `frontera.py` was not under version control. The first commit that holds the patched file is
  [`22fad88`](https://github.com/cmorregof/prometeo/commit/22fad88).

Besides the context fix, the patched file gives a name clash its own label, `NOMBRE_YA_DECLARADO`, and reads the
`#print axioms` line of a name that contains an apostrophe. Changing the judge is a change of protocol. A number on
this page belongs to the judge that produced it.

## How we re-judged

For each run we replayed the attempts in order and rebuilt the context that the fixed harness would have given Lean: the
notebook at the start of the run (empty in all four runs) plus each accepted lemma, once. On that context we judged
again every lemma that had been rejected. We used the judge function `admitir_bloque` from the patched
`unirl/frontera.py` (SHA-256 `59b983ee…`, the same as [`unirl/frontera.py`](../unirl/frontera.py) in this repository).

There are two variants:

- **A (conservative).** The context holds only the lemmas the original judge accepted.
- **B (cascade).** The context also holds the lemmas this re-judging accepts, in the order they would have entered.

Neither variant tells what the model would have done with the correct feedback. Only a new CC run can tell that.

## Results

For the 218 lemmas rejected by a name clash:

| Label after re-judging | A | B |
|---|---:|---:|
| `ACCEPTED` | 184 | 53 |
| `PROOF_FAILED` | 34 | 1 |
| `NOMBRE_YA_DECLARADO` | 0 | 137 |
| `FORBIDDEN` | 0 | 27 |

184 of the 218 lemmas (84 %) were accepted by the patched judge under variant A, and 53 under variant B. In variant
B, 137 lemmas carry a name that a lemma accepted earlier in the cascade already declared, so Lean did not judge their
proofs. Whether an accepted proof is correct is for the reference check of O1 to decide, and that check does not
exist yet.

| Law | A accepted | B accepted |
|---|---:|---:|
| E13102 | 52 of 67 | 5 of 67 |
| E1486_12 | 51 of 60 | 27 of 60 |
| E20911 | 53 of 61 | 16 of 61 |
| E23357 | 28 of 30 | 5 of 30 |

## Checks

- **Control.** The 5 rejections that were not name clashes should keep their label if the context is rebuilt
  correctly. In variant A, all 5 were `PROOF_FAILED` again. In variant B, 3 were `PROOF_FAILED` and 2
  `NOMBRE_YA_DECLARADO`.
- **Axioms.** No lemma was marked unsound because the `#print axioms` line was missing from Lean's output (count: 0).

## The fix

In the CC configuration, the harness wrote each accepted lemma into the notebook and also kept it in the list of the
episode's lemmas. From the next attempt on, Lean saw each of those lemmas twice. The fix adds only the episode's lemmas
that the notebook does not already hold
([`unirl/frontera.py`, lines 573 to 578](https://github.com/cmorregof/prometeo/blob/22fad88/unirl/frontera.py#L573-L578)).
It dates from 24 Oct 2026 and was already in the file when the file entered this repository in commit
[`22fad88`](https://github.com/cmorregof/prometeo/commit/22fad88).

## What is not in this repository

The pilot runs, the re-judging script (`unirl/rejuicio_frontera_cc.py`, SHA-256
`665f80e2054e197196d857ec1153ea2fc358bc7947ed51098bd935a79a83672e`) and its per-lemma output are kept in a private
working copy. The numbers on this page come from the summary that script printed at the end of its run.
