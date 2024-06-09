plot:
	@echo ""
	@echo "-------------------------------------------------------------------------------"
	@echo "  💡 Help  🧠"
	@echo "-------------------------------------------------------------------------------"
	@echo ""
	@echo " Options: "
	@echo "   make                           # Esta ayuda"
	@echo "   make build                     # Construir el container"
	@echo "   make run                       # convertir el PDF"
	@echo "   make run_cardales              # convertir el PDF del directorio cardales"
	@echo "   make shell                     # Abre un shell en el container"
	@echo ""
	@echo ""

CONTAINER_TAG := cardales
APP_DIR := $(shell pwd)

# Build the container -----------------------------------------------------------------------------
build:
	@echo "Building container [tag: ${CONTAINER_TAG}]..."
	@docker build -t ${CONTAINER_TAG} .


# Run the container -------------------------------------------------------------------------------
run:
	@echo "[docker] converting PDFs"
	@docker run -ti --rm -v ${APP_DIR}:/app ${CONTAINER_TAG} python3 convert.py


# Run the container -------------------------------------------------------------------------------
run_cardales:
	@echo "[docker] converting PDFs -> cardales"
	@docker run -ti --rm -v ${APP_DIR}:/app ${CONTAINER_TAG} python3 cardales.py


# Run the container -------------------------------------------------------------------------------
shell:
	@docker run -ti --rm -v ${APP_DIR}:/app ${CONTAINER_TAG} /bin/bash
