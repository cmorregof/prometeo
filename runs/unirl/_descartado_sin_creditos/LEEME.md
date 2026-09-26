# Corridas descartadas: sin créditos en la API de OpenAI (24 sep 2026, 04:45–04:50)

Las diez corridas del PEP (5 variantes abiertas × gpt-6-luna y gpt-6-astra) arrancaron cuando la cuenta de OpenAI ya
no tenía créditos (`429 insufficient_quota`, `credit_balance_exhausted`). Todos sus intentos son PROVIDER_ERROR: el
modelo nunca respondió y el juez nunca evaluó nada. No miden nada y no deben entrar en ningún resumen.
Sus informes están en docs/informes/_descartado_sin_creditos/. Desde esta fecha el bucle aborta la corrida ante un
error de crédito o de autenticación en vez de seguir consumiendo intentos.
