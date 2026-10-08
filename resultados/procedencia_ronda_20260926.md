# Procedencia de las aceptaciones: ronda 20260926-2016

Lectura del 30 sep 2026, sin correr nada, desde los registros de las corridas de la ronda 1 (inicio entre 2026-09-26T20:17:27 y 2026-09-27T14:03:07). Regla de conteo: el primer episodio válido de cada identificador (`unirl/tools/ronda.py`, línea 6). Los `llamadas.jsonl` no se versionan (`.gitignore`): las líneas citadas son de la copia local.

## Qué había en el contexto

* **Glosario sembrado** (25 entradas, E001–E025, clase «glosario»; `runs/unirl/cuaderno/congelados/fbd88bf0474ad117/errores.json`). Entra en el prompt de toda configuración con `glosario=True`, es decir C, C3, E y E3 (`unirl/reflexion.py` en `a5f6c14`, líneas 166–167). Es el entorno base comprobado, no lo aprendido: C y E lo ven igual.
* **Cuaderno aprendido**: solo lo reciben E y E3, y solo la parte de lemas (`unirl/reflexion.py` en `a5f6c14`, líneas 58 y 62). En los 64 episodios de E y E3 el registro dice `errores_mostrados: []` y `estrategias_mostradas: []`. El único lema era `sign_step` (general, admitido en `bis_3_signo#1`). Los lemas mostrados se compilan solos con cada intento (`unirl/reflexion.py` en `a5f6c14`, líneas 254–255; `unirl/cuaderno.py` en `a5f6c14`, líneas 433–434 y 454), así que `sign_step` estaba en la teoría de cada intento de E aunque la prueba no lo citara.
* **C y C3**: sin cuaderno (`--cuaderno ninguno`).

## Tabla

| peldaño | config | modelo | episodio | intento de éxito | consultas | cuaderno en el contexto (id · tipo) | glosario | ¿usa por nombre un lema del cuaderno? | lemas propios en LEMMAS | marcas del martillo | episodio (archivo:línea) | llamada aceptada (archivo:línea) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rf_2_signo | C | luna | `rf_2_signo#C#1` | 1 | 0 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:4` | `runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/llamadas.jsonl:4` |
| rf_2_signo | C | luna | `rf_2_signo#C#2` | 2 | 0 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/evaluacion/20260926-201727-gpt-6-luna/episodios.jsonl:11` | `runs/unirl/rl_verbal/evaluacion/20260926-201727-gpt-6-luna/llamadas.jsonl:14` |
| rf_2_signo | C3 | luna | `rf_2_signo#C3#1` | 3 | 3 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_luna/20260926-201727-gpt-6-luna/episodios.jsonl:2` | `runs/unirl/rl_verbal/pareada_luna/20260926-201727-gpt-6-luna/llamadas.jsonl:6` |
| rf_2_signo | C3 | sol | `rf_2_signo#C3#1` | 2 | 0 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_sol/20260926-201727-gpt-6-sol/episodios.jsonl:1` | `runs/unirl/rl_verbal/pareada_sol/20260926-201727-gpt-6-sol/llamadas.jsonl:3` |
| rf_2_signo | E | luna | `rf_2_signo#E#1` | 1 | 0 | sign_step · lema | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/evaluacion_E/20260927-084149-gpt-6-luna/episodios.jsonl:3` | `runs/unirl/rl_verbal/evaluacion_E/20260927-084149-gpt-6-luna/llamadas.jsonl:3` |
| rf_2_signo | E | luna | `rf_2_signo#E#2` | 3 | 0 | sign_step · lema | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/evaluacion_E/20260927-084149-gpt-6-luna/episodios.jsonl:4` | `runs/unirl/rl_verbal/evaluacion_E/20260927-084149-gpt-6-luna/llamadas.jsonl:6` |
| rf_2_signo | E3 | luna | `rf_2_signo#E3#1` | 3 | 1 | sign_step · lema | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_luna/20260927-084149-gpt-6-luna/episodios.jsonl:2` | `runs/unirl/rl_verbal/pareada_luna/20260927-084149-gpt-6-luna/llamadas.jsonl:5` |
| rf_2_signo | E3 | sol | `rf_2_signo#E3#1` | 2 | 0 | sign_step · lema | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_sol/20260927-084149-gpt-6-sol/episodios.jsonl:1` | `runs/unirl/rl_verbal/pareada_sol/20260927-084149-gpt-6-sol/llamadas.jsonl:3` |
| secante_1_inyectiva | C3 | luna | `secante_1_inyectiva#C3#1` | 3 | 4 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_luna/20260926-233322-gpt-6-luna/episodios.jsonl:5` | `runs/unirl/rl_verbal/pareada_luna/20260926-233322-gpt-6-luna/llamadas.jsonl:22` |
| secante_1_inyectiva | C3 | sol | `secante_1_inyectiva#C3#1` | 2 | 3 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_sol/20260926-233322-gpt-6-sol/episodios.jsonl:3` | `runs/unirl/rl_verbal/pareada_sol/20260926-233322-gpt-6-sol/llamadas.jsonl:12` |
| secante_2_cociente | C | luna | `secante_2_cociente#C#1` | 1 | 3 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:47` | `runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/llamadas.jsonl:126` |
| secante_2_cociente | C | luna | `secante_2_cociente#C#2` | 1 | 3 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/episodios.jsonl:48` | `runs/unirl/rl_verbal/evaluacion/20260926-233322-gpt-6-luna/llamadas.jsonl:127` |
| secante_2_cociente | C3 | luna | `secante_2_cociente#C3#1` | 1 | 4 | ninguno | E001–E025 | no | ninguno | 0/0 | `runs/unirl/rl_verbal/pareada_luna/20260926-233322-gpt-6-luna/episodios.jsonl:7` | `runs/unirl/rl_verbal/pareada_luna/20260926-233322-gpt-6-luna/llamadas.jsonl:26` |

**Resultado.** 13 pruebas aceptadas. 0 usan por nombre un lema del cuaderno. Ninguna declara lemas propios ni usa marcas `by martillo`. En E y E3, `sign_step` estaba compilado en la teoría pero ninguna prueba aceptada lo invoca: las aceptaciones de E no dependen del cuaderno.

Comprobación: la búsqueda del nombre se hizo sobre `proof`, `prueba_final` y `lemmas` de la llamada aceptada, como palabra completa.

## Anexo A. McNemar ampliado (copia)

Copia de lo añadido el 30 sep 2026 a `resultados/RONDA_TERMINADA.md`. Hace falta la copia porque la ronda 2, al terminar, escribe su propio `RONDA_TERMINADA.md` con el mismo nombre.

Recalculado el 30 sep 2026 desde los `episodios.jsonl` de las corridas de esta ronda (inicio entre 2026-09-26T20:17:27 y 2026-09-27T14:03:07), sin correr nada y con la misma regla: cuenta el primer episodio válido. H2 prerregistrada es E frente a C (`docs/formulacion/formulacion_rl_verbal.tex`, líneas 205 y 222); estas comparaciones son exploratorias. C difiere de B en la reflexión y además en los intentos (4 frente a 1); de B0, también en el glosario y las consultas (`unirl/reflexion.py` en `a5f6c14`, líneas 52–54).

| comparación | unidad | pares | gana C | gana el otro | p exacto bilateral |
|---|---|---|---|---|---|
| Luna: C frente a B0 | peldaño y episodio (2 por peldaño) | 32 | 6 | 0 | 0.0312 |
| Luna: C frente a B0 | peldaño (cerrado si algún episodio lo cerró) | 16 | 3 | 0 | 0.25 |
| Luna: C frente a B | peldaño y episodio (2 por peldaño) | 32 | 3 | 1 | 0.625 |
| Luna: C frente a B | peldaño (cerrado si algún episodio lo cerró) | 16 | 1 | 1 | 1.0 |

Pares discordantes, como (peldaño, episodio, y_C, y_otro):

* C frente a B0: [['rf_1_punto', 1, 1, 0], ['rf_1_punto', 2, 1, 0], ['rf_2_signo', 1, 1, 0], ['rf_2_signo', 2, 1, 0], ['secante_2_cociente', 1, 1, 0], ['secante_2_cociente', 2, 1, 0]]
* C frente a B: [['rf_2_signo', 1, 1, 0], ['rf_2_signo', 2, 1, 0], ['rf_4_raiz', 2, 0, 1], ['secante_2_cociente', 1, 1, 0]]

Sensibilidad a la regla del primer válido: `rf_2_signo#B#2` se corrió dos veces; la primera falló y la repetición se aceptó. Con la regla del último válido, C frente a B por episodio quedaría 2 a 1 (p = 1.0).

## Anexo B. Prueba aceptada de rf_3_encaje (Sol, E3)

Episodio `rf_3_encaje#E3#1`, intento 3, sin consultas, sin marcas del martillo. Registro: `runs/unirl/rl_verbal/pareada_sol/20260927-084149-gpt-6-sol/llamadas.jsonl:9`. En el contexto estaba `sign_step · lema`; la prueba no lo usa y declara su propio lema `rf_position`.

LEMMAS:

```isabelle
lemma rf_position:
  fixes l u :: real
  assumes lu: "l < u"
    and fl: "f l < 0"
    and fu: "0 \<le> f u"
  shows "l < punto_rf f l u \<and> punto_rf f l u \<le> u"
proof -
  (* El denominador es positivo y no nulo. *)
  have dpos: "0 < f u - f l" using fl fu by linarith
  have dne: "f u - f l \<noteq> 0" using dpos by linarith

  (* Expresamos las distancias a los extremos como cocientes. *)
  have left:
    "punto_rf f l u - l = (u - l) * (- f l) / (f u - f l)"
    using dne by (simp add: punto_rf_def field_simps algebra_simps)
  have right:
    "u - punto_rf f l u = (u - l) * f u / (f u - f l)"
    using dne by (simp add: punto_rf_def field_simps algebra_simps)

  (* La distancia al extremo izquierdo es positiva. *)
  have left_num: "0 < (u - l) * (- f l)"
    using lu fl by (intro mult_pos_pos) auto
  have left_quot: "0 < (u - l) * (- f l) / (f u - f l)"
    using left_num dpos by (rule divide_pos_pos)
  have left_pos: "0 < punto_rf f l u - l"
    using left_quot by (simp only: left)

  (* La distancia al extremo derecho es no negativa. *)
  have right_num: "0 \<le> (u - l) * f u"
    using lu fu by (intro mult_nonneg_nonneg) auto
  have right_quot: "0 \<le> (u - l) * f u / (f u - f l)"
    using right_num dpos by simp
  have right_nonneg: "0 \<le> u - punto_rf f l u"
    using right_quot by (simp only: right)

  show ?thesis using left_pos right_nonneg by linarith
qed
```

PROOF:

```isabelle
proof -
  let ?R = "regula_falsi f a b"
  let ?P = "\<lambda>k. a \<le> fst (?R k) \<and>
    fst (?R k) < snd (?R k) \<and> snd (?R k) \<le> b \<and>
    f (fst (?R k)) < 0 \<and> 0 \<le> f (snd (?R k))"

  (* Inducimos simultáneamente sobre los límites y los signos de la horquilla. *)
  have invariant: "\<And>k. ?P k"
  proof -
    fix k
    show "?P k"
    proof (induction k)
      case 0
      show ?case using ab fa fb by simp
    next
      case (Suc k)
      obtain l u where old: "?R k = (l, u)"
        by (cases "?R k") auto
      have al: "a \<le> l" and lu: "l < u" and ub: "u \<le> b"
        and fl: "f l < 0" and fu: "0 \<le> f u"
        using Suc.IH old by auto
      let ?p = "punto_rf f l u"

      (* La interpolación avanza desde l sin sobrepasar u. *)
      have lp: "l < ?p" and pu: "?p \<le> u"
        using rf_position[OF lu fl fu] by auto

      show ?case
      proof (cases "f l * f ?p \<le> 0")
        case True
        (* El nuevo extremo derecho tiene valor no negativo. *)
        have fp: "0 \<le> f ?p"
        proof (rule ccontr)
          assume "\<not> 0 \<le> f ?p"
          then have "f ?p < 0" by simp
          then have "0 < f l * f ?p"
            using fl by (simp add: mult_neg_neg)
          with True show False by linarith
        qed
        have updated: "?R (Suc k) = (l, ?p)"
          using old True by simp
        show ?thesis using al lp pu ub fl fp updated by auto
      next
        case False
        (* En esta rama el valor del punto interpolado es negativo. *)
        have fp: "f ?p < 0"
        proof (rule ccontr)
          assume "\<not> f ?p < 0"
          then have fp_nonneg: "0 \<le> f ?p" by simp
          have "f l * f ?p \<le> 0"
            using fl fp_nonneg by (intro mult_nonpos_nonneg) auto
          with False show False by simp
        qed

        (* El punto no puede coincidir con u, cuyo valor es no negativo. *)
        have pu_strict: "?p < u"
        proof (rule ccontr)
          assume "\<not> ?p < u"
          then have "?p = u" using pu by linarith
          with fp fu show False by simp
        qed
        have updated: "?R (Suc k) = (?p, u)"
          using old False by simp
        show ?thesis using al lp pu_strict ub fp fu updated by auto
      qed
    qed
  qed

  (* Aplicamos el invariante a la horquilla n. *)
  obtain l u where old: "?R n = (l, u)"
    by (cases "?R n") auto
  have al: "a \<le> l" and lu: "l < u" and ub: "u \<le> b"
    and fl: "f l < 0" and fu: "0 \<le> f u"
    using invariant[of n] old by auto
  let ?p = "punto_rf f l u"
  have lp: "l < ?p" and pu: "?p \<le> u"
    using rf_position[OF lu fl fu] by auto

  (* La actualización sustituye exactamente uno de los extremos. *)
  have updated: "?R (Suc n) = (l, ?p) \<or> ?R (Suc n) = (?p, u)"
    using old by (cases "f l * f ?p \<le> 0") auto
  show ?thesis using al lu ub lp pu old updated by auto
qed
```
