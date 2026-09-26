# ESTRUCTURA_OBJETIVO.md · `rl_metodos`

Estructura de destino para la rama `reorganizar`. Principios: **un paquete, un `.venv`, un `pyproject.toml`, un
`LICENSE`, un `.gitignore`**; todo registro de corrida bajo un solo `runs/`; nada científico se borra. Los nombres
de importación de los paquetes didácticos cambian a `didactica.<nombre>` (dos laboratorios los usan; se actualizan).
`steprl`, `unirl` e `isarl` conservan su nombre de importación; `isarl` vive en `isarl/` (ver §1; el texto anterior
decía `isabelle/` por error).

---

## 1. Árbol de destino

```
rl_metodos/
  pyproject.toml            # ÚNICO. Paquetes: unirl, steprl, isarl, didactica.*  Extras: [dev]
  README.md                 # reescrito al final con las cifras auditadas (resultados/auditoria_cifras.md)
  LICENSE                   # uno solo (los siete son idénticos)
  CLAUDE.md                 # el actual, con rutas actualizadas
  .gitignore                # uno solo, en la raíz (§4); se eliminan los .gitignore de subcarpetas
  MIGRACION.md              # tabla ruta vieja → ruta nueva, generada por la migración

  unirl/                    # ← 09_unified/unirl/   (entorno, jueces, RL verbal, cuaderno). Sin cambios de nombre.
    configs/  tools/        # ← 09_unified/configs/, tools/ (código y configuración: dentro del paquete)
    isabelle_commands.txt   # ← 09_unified/targets/isabelle_commands.txt (dato del filtro léxico: código)
  steprl/                   # ← 06_stepsizes/steprl/ (juez PEP: verificador SDP y certificados). Sin cambios de nombre.
  isarl/                    # ← 08_isabelle/isarl/  (juez Isabelle: martillo, sandbox, reproducción Tabla 1)
  didactica/                # ← 01–05 y 07, como SUBPAQUETES; cada uno conserva sus env_proof/trainer/tui/report/cli
    __init__.py
    qagent.py               # el agent.py compartido, UNA vez (los seis son idénticos: comprobado)
    __main__.py             # el común (despachador); cada subpaquete conserva su __main__.py para `python -m didactica.<metodo>`
    biseccion/              # ← 01_biseccion/bisectrl/      (import: didactica.biseccion)
    punto_fijo/             # ← 02_punto_fijo/fixpointrl/
    taylor/                 # ← 03_taylor/taylorrl/
    newton/                 # ← 04_newton/newtonrl/
    secante/                # ← 05_secante/secantrl/
    interpolacion/          # ← 07_interpolacion/interprl/

  corpus/
    curado/
      raices/               # ← 09_unified/corpus/raices/  (los 48 peldaños, sus validaciones y revision_enunciados.md)
      programas/            # ← 09_unified/targets/{bisection,countdown}.json y _bisection_aux.thy.part (objetivos del juez de programa)
      stepsize/             # ← 09_unified/targets/gd_*.json y gd_cert/ (objetivos del juez de teorema y sus certificados)
    existencia/             # VACÍO por ahora (se llenará con AFP/HOL-Analysis con pruebas ocultas). Solo un LEEME.md

  certificados/             # ← 06_stepsizes/certificados/ (los certificados PEP versionados; n = 6 sigue marcado como no resuelto)

  runs/                     # INTOCABLE en contenido. Solo se MUEVE, con SHA-256 antes/después.
    didactica/
      biseccion/<fecha>/    # ← 01_biseccion/runs/*
      punto_fijo/…  taylor/…  (02, 03; 04 y 05 no tienen runs propios)
    pep/<fecha>/            # ← 06_stepsizes/runs/*  (y sus archivos sueltos: cert-*.json, evolve-*.log, refs-*.log)
    isabelle/               # ← 08_isabelle/runs/*  (repro_bisection.json …)
    unirl/                  # ← 09_unified/runs/*   (rl_verbal/, _baseline/, bisection_isabelle_lemas_mem/, …)
      cuaderno/             # ← 09_unified/cuaderno/  (estado vivo del cuaderno del RL verbal)
      bisection_isabelle_lemas_mem/20260923-224900-gpt-6-astra-high/
        codigo_unirl_61c5c2b8.tar.gz   # ← .snap_astra_bis/ comprimido (B4); luego .snap_astra_bis/ se borra
    corridas_locales/       # ← resultados/corridas_locales/

  logs/                     # ← 09_unified/logs/ (gasto.json, caché SQLite, candados, *.log)
                            #   + los cuatro registros sueltos de la raíz de 09 (B7) y runs_repro.log de 08, con un LEEME.md

  resultados/               # ← resultados/ (inventario, métricas, estadística, informe_estado, auditoria_cifras, tablas/)
                            #   + los seis archivos de 09_unified/resultados/; sin corridas_locales/ (van a runs/)

  docs/
    formulacion/            # ← 09_unified/docs/nota/  (formulacion_rl_verbal.tex, unirl_definicion.tex/.pdf, .bib maestro)
                            #   + PLAN_rl_verbal.md, RELANZAMIENTO.md, unirl_README.md, diseno_gd_isabelle.md
    informes/               # ← 09_unified/docs/informes/  SIN _descartado_sin_creditos/ (B6: git rm); + reproduccion-bisection.md (08)
    curso/                  # ← docs/curso/  (lab01, lab02, tex/, pdf/; se fija Markdown como fuente, LaTeX derivado)
    ejecuciones_pep/        # ← 06_stepsizes/docs/ejecucion-*.md

  tests/
    didactica/              # ← tests de 01–05 y 07
    steprl/                 # ← tests de 06
    unirl/                  # ← tests de 09 (rápidas e Isabelle; fixtures/pruebas_privadas/ sigue ignorado) + test_isarl.py
    conftest.py

  .github/workflows/tests.yml   # un solo flujo: pytest tests/didactica tests/steprl tests/unirl -m "not isabelle"
```

`goldbach_operador/` **no entra** en esta reorganización: es otro repo con otro verificador (Lean) y se ordena aparte
después de su primer commit.

---

## 2. Decisiones que responden a los hechos levantados

1. **Los módulos que difieren no se fusionan.** `env_proof.py`, `trainer.py`, `tui.py`, `report.py`, `cli.py` e
   `__init__.py` se mueven tal cual a su subpaquete. Solo se comparte `qagent.py`. Cada `agent.py` se elimina y su
   importación pasa a `from ..qagent import QAgent`. Los `__main__.py` de cada subpaquete se conservan.
2. **`unirl` deja de usar `sys.path`.** Los `sys.path.insert` hacia `06_stepsizes` y `08_isabelle` se sustituyen por
   `import steprl` / `import isarl`, que ya resuelven con el paquete único instalado en modo editable.
3. **Los laboratorios del curso** cambian `from bisectrl …` → `from didactica.biseccion …` y `fixpointrl` →
   `didactica.punto_fijo`. Son los únicos consumidores externos. Las guías y notas del curso (Markdown y LaTeX) no se
   tocan: son material ya usado en clase y su texto es histórico.
4. **`resultados/consolidar.py`** y cualquier script que lea `runs/` por ruta relativa se actualiza a las rutas nuevas;
   volver a correrlo y comprobar que `resumen.json` y `metricas.csv` salen **idénticos** (salvo las rutas de la columna
   `fuente` y el commit de HEAD) es la prueba de que la migración de `runs/` no perdió nada.
5. **`.venv` único:** crearlo NUEVO desde el `pyproject.toml` (`pip install -e ".[dev]"`, con red) **antes** de borrar
   los ocho viejos; los viejos se borran solo cuando `pytest` completo esté en verde con el nuevo.
6. **08 no tiene pruebas.** Se escribe una mínima (que `isarl` importa y que `repro_bisection.json` se lee y tiene 15
   VCs); la carpeta vacía `08_isabelle/tests/` desaparece.
7. **Carpetas vacías** (`06_stepsizes/06_stepsizes/`, `07_interpolacion/docs/`) se eliminan.
8. **Los objetivos congelados del juez Isabelle son enunciados**, así que van a `corpus/curado/` por dominio
   (`programas/`, `stepsize/`); `isabelle_commands.txt` es un dato del filtro léxico y se queda en `unirl/`.
9. **El cuaderno es estado de las corridas del RL verbal**: `runs/unirl/cuaderno/`, no la raíz.

---

## 3. Qué se borra y qué se mueve

| acción | qué |
|---|---|
| **borrar** (regenerable) | los ocho `.venv/` (tras §2.5), `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.DS_Store`, auxiliares de LaTeX (`aux log out fls fdb_latexmk bbl blg listing`), `docs/curso/tex/*.pdf` (duplicados), `.snap_astra_bis/` (tras el tar de §1), seis `LICENSE` repetidos, cinco `agent.py` repetidos |
| **git rm** (recuperable en historia) | `09_unified/docs/nota/unirl_definicion_v0.2_preliminar.pdf` (B5), `09_unified/docs/informes/_descartado_sin_creditos/` (B6) |
| **mover con SHA-256 antes/después** | todo `runs/`, `logs/`, `corpus/`, `cuaderno/`, `certificados/`, `*.jsonl`, `gasto.json`, `tests/fixtures/pruebas_privadas/`, los `.dat`/`.json` de resultados |
| **git mv** (código y docs) | todo lo demás |
| **no tocar** | `.git/`, el `.env` de 06 (se mueve a la raíz como `.env`, ignorado; NUNCA se imprime ni se copia a manifiestos) |

---

## 4. `.gitignore` único de la raíz

```
.venv/
__pycache__/
*.egg-info/
.pytest_cache/
.DS_Store
.env
*.aux *.log *.out *.fls *.fdb_latexmk *.bbl *.blg *.listing
docs/curso/tex/*.pdf
# corridas: se versiona la estructura y los informes, no los registros pesados
runs/**/llamadas.jsonl
logs/*.sqlite
logs/*.lock
logs/**/*.pid
tests/unirl/fixtures/pruebas_privadas/
runs/didactica/**
runs/pep/**
# material ajeno y paquetes recibidos: nunca
Conjeturas/
*.zip
Convocatoria*
.snap_*/
```

(`runs/isabelle/`, `runs/unirl/` y `runs/corridas_locales/` se versionan, como hoy 08 y 09. Los `.log` de `logs/` que
son registros de corridas, no de LaTeX, se reincluyen con `!logs/*.log`.)

---

## 5. Criterios de terminación

1. `pytest` completo en verde en el `.venv` nuevo (hoy: 77 en didáctica/steprl, 167 rápidas en unirl; las de
   Isabelle se corren si `~/isabelle/Isabelle2025.app` existe, si no se omiten con marca).
2. `didactica.biseccion` con semilla 1: λ = ½ en la generación 345 y Bolzano en 358 (calibración de `CLAUDE.md`).
   Es la prueba de que la fusión no cambió el comportamiento.
3. `resultados/consolidar.py` reproduce `resumen.json` y `metricas.csv` sin diff (salvo rutas y HEAD).
4. Manifiesto SHA-256 «después» de lo intocable idéntico al «antes» (363 archivos, 7,3 MB) salvo las rutas.
5. `git status` limpio; un commit por paso en `reorganizar`; **sin push**; **sin llamadas a la API**.
6. `MIGRACION.md` escrito y `CLAUDE.md` con las rutas nuevas.

---

## 6. Reservado para la tesis (NO crear ahora; solo para que la estructura no se rehaga)

* `corpus/existencia/<dominio>/` — lemas del AFP / HOL-Analysis / seL4 con pruebas ocultas, por estrato
  (análisis, software verificado, topología).
* `corpus/curado/<dominio>/` — futuros peldaños aprobados a mano (interpolación, cuadratura, programas).
* Un quinto juez, Lean, vivirá en `unirl/verifiers/` cuando `goldbach_operador` se conecte; su corpus sigue en el otro
  repo.
* `runs/<juez>/<dominio>/<fecha>/` es la convención para todo lo nuevo.

---

## Ajustes al documento original (26–27 sep 2026, decisiones de Carlos tras la migración)

* Preámbulo: `isarl/`, no `isabelle/`.
* §1: `runs/unirl/cuaderno/` (el cuaderno es estado de corridas); `corpus/curado/{programas,stepsize}/` (los objetivos
  del juez Isabelle son enunciados); `unirl/isabelle_commands.txt`; los encajes provisionales de `MIGRACION.md` §4,
  aceptados (READMEs y capturas junto a su paquete, `configs/` y `tools/` dentro de `unirl/`, los seis archivos de
  `09_unified/resultados/` en `resultados/`, el plan y el relanzamiento en `docs/formulacion/`, la reproducción de la
  Tabla 1 en `docs/informes/`, `runs_repro.log` en `logs/`, los sueltos de 06 en `runs/pep/`).
* §2.1: se conservan los `__main__.py` por subpaquete. §2.3: las guías y notas del curso no se tocan. §2.8 y §2.9 nuevos.
* §3: cinco `agent.py` repetidos (el sexto es `qagent.py`).
