# The pilot judge

These four files are the harness and Lean judge that judged the pilot runs of 24 Oct 2026, before the name-clash fix
described in [pilot_rejudging.md](../pilot_rejudging.md#two-judges). They are kept here byte for byte so the recorded
fingerprint can be checked. They are not meant to be run from this folder: they import other modules of `unirl/` with
relative imports.

`juez_lean.py`, `loop.py` and `gasto.py` are identical to the files of the same name in [`unirl/`](../../unirl/).
`frontera.py` is the version before the fix; the patched version is [`unirl/frontera.py`](../../unirl/frontera.py).

## The fingerprint

Each pilot run wrote a field `codigo` in its `meta.json`. The function `_huella_codigo()` in `frontera.py` computes it:
it feeds the bytes of `frontera.py`, `juez_lean.py`, `loop.py` and `gasto.py`, in that order and with nothing between
them, into one SHA-256 hash, and keeps the first 16 hexadecimal characters. The four pilot runs recorded
`4dde23ec5862dde9`.

| File | SHA-256 |
|---|---|
| `frontera.py` | `3ef64496f1a5a4d458bbdc9b4fe87b52eb1de5512e2bff16133cd1b3fe9b55bf` |
| `juez_lean.py` | `08c16dbe1b93e27cf21e8ca4fa4ca2813ace22cad249365b9bf0e616154b0b49` |
| `loop.py` | `809abc2eb09b2947f13785b8fbda167445a9d72bd50287215135124cc339c2a7` |
| `gasto.py` | `38d692793317247c706002ca1b13c7ad38b2dcadc4a314e493fe1749ab5dc017` |

From the repository root:

```bash
cat tantalus/pilot_judge/frontera.py tantalus/pilot_judge/juez_lean.py tantalus/pilot_judge/loop.py tantalus/pilot_judge/gasto.py | shasum -a 256 | cut -c1-16
```

It prints `4dde23ec5862dde9`.
