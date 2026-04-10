## DESAR Server - Makefile

BINARY = desar-server
BUILD_DIR = ./bin
MAIN = ./cmd/server/main.go

.PHONY: build run clean deploy deps

## Instalar dependencias
deps:
	go mod tidy
	go mod download

## Compilar binario Linux AMD64
build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
		go build -ldflags="-s -w" -o $(BUILD_DIR)/$(BINARY) $(MAIN)
	@echo "Binario: $(BUILD_DIR)/$(BINARY)"

## Ejecutar en desarrollo
run:
	API_PORT=8443 WEB_PORT=8080 \
	DBS_PATH=./data \
	JWT_SECRET=dev-secret-cambia-en-prod \
	go run $(MAIN)

## Limpiar
clean:
	rm -rf $(BUILD_DIR)

## Deploy al servidor (ajusta IP y ruta)
## Uso: make deploy SERVER=usuario@ip
deploy: build
	@if [ -z "$(SERVER)" ]; then echo "Uso: make deploy SERVER=user@ip"; exit 1; fi
	ssh $(SERVER) "mkdir -p /opt/desar-server/data"
	scp $(BUILD_DIR)/$(BINARY) $(SERVER):/opt/desar-server/
	scp configs/desar.service   $(SERVER):/tmp/
	ssh $(SERVER) "sudo mv /tmp/desar.service /etc/systemd/system/ && \
		sudo systemctl daemon-reload && \
		sudo systemctl enable desar-server && \
		sudo systemctl restart desar-server && \
		sudo systemctl status desar-server"
	@echo "✅ Desplegado en $(SERVER)"

## Ver logs en servidor
logs:
	@if [ -z "$(SERVER)" ]; then journalctl -u desar-server -f; \
	else ssh $(SERVER) "journalctl -u desar-server -f"; fi
