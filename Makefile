.PHONY: run build tidy deploy clean

BIN=desar-server

run: tidy
	go run ./cmd/server/

build: tidy
	go build -o $(BIN) ./cmd/server/

tidy:
	go mod tidy

clean:
	rm -f $(BIN) data/admin.db data/company_*.db

# Deploy to remote server
deploy:
	@test -n "$(SERVER)" || (echo "Usage: make deploy SERVER=user@host"; exit 1)
	go build -o $(BIN) ./cmd/server/
	ssh $(SERVER) "mkdir -p /opt/desar/{data,web}"
	scp $(BIN) $(SERVER):/opt/desar/
	scp -r web/templates web/static $(SERVER):/opt/desar/web/
	scp configs/desar.service $(SERVER):/etc/systemd/system/
	scp configs/nginx.conf $(SERVER):/etc/nginx/sites-available/desar
	ssh $(SERVER) "systemctl daemon-reload && systemctl restart desar"
	@echo "✅ Deploy OK"

# Reset SQLite DBs (dev only)
reset-db:
	rm -f data/admin.db data/company_*.db
	@echo "✅ DBs eliminadas, se recrearán en el próximo run"

# Crear BD admin PostgreSQL
pg-setup:
	createdb desar_admin || true
	@echo "✅ desar_admin lista"
