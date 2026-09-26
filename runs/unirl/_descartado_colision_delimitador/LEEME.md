Corrida de gpt-5.4-mini (low) bajo V_I, 23 sep 2026 18:23–19:18. Descartada: en 4 de 12 intentos el modelo
terminó el variante en «\<rceil>>>» y el extractor tomó «\<rceil» (símbolo sin cerrar) → VCG_FAILED por un
defecto del protocolo de respuesta (el delimitador «>>>» colisiona con los símbolos de Isabelle que terminan en «>»),
no por un error del modelo. Se corrigió el extractor (cierra un símbolo final sin cerrar) y se repitió la corrida.
Con el extractor corregido, las 12 propuestas de gpt-6-luna no cambian.
