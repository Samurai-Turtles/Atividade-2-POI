PORT ?= 8000
WEB_CONCURRENCY ?= 1
TAMANHO_MAXIMO ?= 1000
IMAGEM ?= cpu-bound-app
CONTAINER ?= cpu-bound-app

export PORT WEB_CONCURRENCY TAMANHO_MAXIMO

.PHONY: help install run docker-build docker-run docker-stop

help:
	@echo "Execução local (com o ambiente Python ativado):"
	@echo "  make install       Instala as dependências"
	@echo "  make run           Inicia a aplicação com Uvicorn"
	@echo "Execução via contêiner:"
	@echo "  make docker-build  Constrói a imagem"
	@echo "  make docker-run    Executa o contêiner"
	@echo "  make docker-stop   Para o contêiner"
	@echo "Variáveis: PORT=$(PORT) WEB_CONCURRENCY=$(WEB_CONCURRENCY) TAMANHO_MAXIMO=$(TAMANHO_MAXIMO)"

install:
	pip install -r requirements.txt

run:
	uvicorn app:app --app-dir src --host 0.0.0.0 --port $(PORT) --workers $(WEB_CONCURRENCY) --no-access-log

docker-build:
	docker build -t $(IMAGEM) .

docker-run:
	docker run --rm --name $(CONTAINER) -p $(PORT):$(PORT) \
		-e PORT -e WEB_CONCURRENCY -e TAMANHO_MAXIMO $(IMAGEM)

docker-stop:
	docker stop $(CONTAINER)
