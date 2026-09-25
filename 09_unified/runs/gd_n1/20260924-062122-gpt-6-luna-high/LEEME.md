# Luna, gd_n1: corrida con el analizador de respuestas anterior

Esta corrida empezó el 24 sep 2026 a las 06:21, antes de que se corrigiera `TheoremVerifier.parse` (06:50), y cada
proceso carga el código al empezar. Con el analizador anterior, una respuesta con `LEMMAS: <<<>>` (dos '>' en vez
de tres, para decir «sin lemas») hacía que el bloque de lemas se comiera la demostración: el intento salía
INVALID_PROPOSAL con el motivo «el bloque de lemas debe empezar con `lemma`», y la demostración nunca llegaba a
Isabelle. Le pasó a Luna en 4 de sus 12 intentos. Los otros 8 son PROOF_FAILED genuinos (Isabelle rechazó la
demostración). Astra corre gd con el analizador corregido; en gd_n1 la comparación entre modelos no es limpia.
Luna usa el analizador corregido desde gd_const_n2.
