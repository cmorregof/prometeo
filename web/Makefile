# Regenera las grabaciones que reproduce el visor (no entrena nada en el navegador).
# Usa el .venv de la raíz del repo.
.PHONY: data dev build deploy
data:
	cd .. && .venv/bin/python -m didactica.historia --all --record web/public/data --every 2
dev:
	npm run dev
build:
	npm run build
deploy:
	vercel --prod
