# Variáveis sobrescrevíveis: make docker-run MEM=2g CPUS=2 WORKERS=2
WORKERS ?= 2
PORT    ?= 8000
IMAGE   ?= memory-bound
MEM     ?= 2g
CPUS    ?= 2

# Experimento (make experiment CENARIO=meu-cenario)
CENARIO ?= local
URL     ?= http://localhost:$(PORT)
SIZE    ?= 256
DUR     ?= 60s
LEVELS  ?= 1 4 8 16 32
PASSES  ?= 3

.PHONY: help install run docker-build docker-run docker-stop experiment load clean

help:
	@echo "install       cria .venv e instala dependências"
	@echo "run           sobe a API localmente (uvicorn)"
	@echo "docker-build  constrói a imagem"
	@echo "docker-run    sobe o container (limites MEM e CPUS)"
	@echo "docker-stop   para o container"
	@echo "experiment    roda o hey em vários níveis de concorrência"
	@echo "load          roda a collection Postman via Newman"
	@echo "clean         remove .venv e caches"

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

run:
	.venv/bin/uvicorn main:app --host 0.0.0.0 --port $(PORT) --workers $(WORKERS)

docker-build:
	docker build -t $(IMAGE) .

docker-run: docker-build
	docker run --rm -d --name $(IMAGE) -p $(PORT):8000 \
		-e WORKERS=$(WORKERS) --memory=$(MEM) --cpus=$(CPUS) $(IMAGE)

docker-stop:
	docker stop $(IMAGE)

experiment:
	PASSES=$(PASSES) MONITOR=1 ./experiments/run_experiment.sh $(CENARIO) $(URL) $(SIZE) $(DUR) "$(LEVELS)"

load:
	./postman/run-load.sh 50 $(URL) $(SIZE)

clean:
	rm -rf .venv __pycache__
