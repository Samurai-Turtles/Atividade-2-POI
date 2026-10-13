# App Memory-bound

Backend simples (apenas API HTTP) com perfil **memory-bound**, desenvolvido para a Atividade 2 (relação entre demanda, desempenho, utilização de recursos e provisionamento).

## Sumário

- [O que a aplicação faz](#o-que-a-aplicação-faz)
- [Por que é memory-bound](#por-que-é-memory-bound)
- [Requisitos](#requisitos)
- [Como rodar](#como-rodar)
- [Endpoints](#endpoints)
- [Testando](#testando)
- [Teste de carga](#teste-de-carga)
- [Teste de carga com Postman](#teste-de-carga-com-postman)
- [Experimentos automatizados (hey)](#experimentos-automatizados-hey)
- [Parâmetros para os experimentos](#parâmetros-para-os-experimentos)
- [Estrutura do projeto](#estrutura-do-projeto)

## O que a aplicação faz

A cada requisição em `/memory`, o servidor:

1. aloca um buffer de `size_mb` MB e escreve em todas as páginas;
2. realiza `passes` passadas de acessos em posições aleatórias do buffer;
3. devolve o tempo gasto e um checksum (para o trabalho não ser descartado).

## Por que é memory-bound

- O buffer é muito maior que o cache da CPU, e os acessos são aleatórios. Quase todo acesso vira *cache miss* e o tempo passa a depender da latência e da largura de banda da memória, não de cálculo.
- O buffer fica alocado enquanto a requisição é atendida. Com N requisições simultâneas, o consumo de RAM é de aproximadamente **N × `size_mb`**. Quando isso passa da memória da VM, aparecem swap e degradação (ou o processo é morto pelo OOM killer).

## Requisitos

- Python 3.10 ou superior
- Dependências em [requirements.txt](requirements.txt): `fastapi`, `uvicorn`, `numpy`

## Como rodar

```bash
cd memory-app
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

- `--host 0.0.0.0` deixa a API acessível de fora da máquina (necessário na VM, junto com o redirecionamento de portas do VirtualBox).
- `--workers` define o número de processos. Cada worker atende requisições em paralelo, então varie esse valor junto com o número de CPUs da VM.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Retorna `{"status": "ok"}`. Serve para checar se o serviço está no ar. |
| GET | `/memory` | Executa a carga memory-bound. |

Parâmetros de `/memory`:

| Parâmetro | Padrão | Limites | Descrição |
|-----------|--------|---------|-----------|
| `size_mb` | 64 | 1 a 2048 | Tamanho do buffer alocado, em MB. |
| `passes` | 1 | 1 a 100 | Número de passadas de acesso aleatório. |

Exemplo de resposta:

```json
{"size_mb": 64, "passes": 1, "checksum": 8794914608779, "elapsed_ms": 75.46}
```

## Testando

```bash
curl localhost:8000/health
curl "localhost:8000/memory?size_mb=64"
curl "localhost:8000/memory?size_mb=256&passes=3"
```

A documentação interativa (Swagger) fica em `http://localhost:8000/docs`.

## Teste de carga

Exemplo com [hey](https://github.com/rakyll/hey), com 20 conexões simultâneas durante 30 segundos:

```bash
hey -z 30s -c 20 "http://localhost:8000/memory?size_mb=64"
```

Para observar a utilização de recursos durante o teste, use em outro terminal, por exemplo:

```bash
vmstat 1          # memória, swap, CPU
top               # consumo por processo
```

### Exemplo de teste pesado

Para forçar pressão de memória, escolha `size_mb` e a concorrência de forma que **concorrência × `size_mb`** fique próximo (ou acima) da RAM livre da VM. Exemplo para uma VM com 2 GB, em que 20 requisições simultâneas de 256 MB pedem cerca de 5 GB:

```bash
# na VM: 256 MB por requisição, 3 passadas, 60 s por nível, coletando CPU e memória
PASSES=3 MONITOR=1 ./experiments/run_experiment.sh vm-2cpu-2gb-pesado http://localhost:8000 256 60s "1 4 8 16 32"
```

Para um teste isolado, sem o script: `hey -z 60s -c 16 "http://localhost:8000/memory?size_mb=256&passes=3"`.

O que observar: aumento do tempo de resposta, uso de swap (`vmstat 1`, colunas `si`/`so`) e eventuais processos mortos pelo OOM killer (`dmesg | grep -i "killed process"`). Se o uvicorn for morto, o `hey` passa a registrar erros de conexão. Isso também é um resultado válido para o relatório. Comece com concorrências menores para não travar a VM.

## Teste de carga com Postman

A pasta [postman/](postman/) tem uma collection pronta, em um único arquivo JSON:

- `memory-bound.postman_collection.json`: variáveis `base_url`, `size_mb`, `passes` e `max_response_ms` (editáveis na aba *Variables* da collection) e 5 requisições (health, leve 16 MB, médio 64 MB, pesado 256 MB e uma parametrizada por `size_mb` e `passes`). Todas validam status 200 e tempo de resposta máximo.

**Pelo app do Postman:** importe o arquivo e use o *Collection Runner* com o número de iterações desejado. Para carga com usuários virtuais simultâneos, use *Run collection > Performance* (disponível no app, com limites no plano gratuito). Na VM, troque a variável `base_url` da collection pelo IP e porta da VM.

**Pela linha de comando (Newman):**

```bash
./postman/run-load.sh 50 http://localhost:8000 64   # iterações, base_url, size_mb
```

O script gera um JSON com os resultados em `postman/results/`.

> O Collection Runner e o Newman enviam as requisições **em sequência**, sem concorrência. Eles medem tempo de resposta, mas não aumentam a demanda por si só. Para variar a concorrência (e ver o consumo de RAM crescer), use o modo Performance do Postman ou o `hey` da seção anterior.

## Experimentos automatizados (hey)

A pasta [experiments/](experiments/) tem dois scripts:

- `run_experiment.sh`: roda o `hey` em vários níveis de concorrência e grava tudo em `experiments/results/<cenario>/`: `resultados.csv` (uma linha por nível: vazão, tempo médio, P50/P90/P95/P99, respostas 200, outras respostas e erros) e `c<N>-hey.txt` (saída bruta de cada nível). **Se a pasta do cenário já existir, ela é apagada** antes de a nova execução começar.
- `monitor.sh`: amostra CPU, memória e swap a cada segundo em CSV. Deve rodar **na máquina do servidor**.

Uso:

```bash
./experiments/run_experiment.sh <cenario> [base_url] [size_mb] [duracao] ["niveis de concorrencia"]

# exemplo: cenário "vm-2cpu-2gb", 64 MB por requisição, 30 s por nível
./experiments/run_experiment.sh vm-2cpu-2gb http://localhost:8000 64 30s "1 5 10 20 40"
```

Como coletar CPU e memória:

- **Rodando o script dentro da VM** (contra `localhost`): use `MONITOR=1 ./experiments/run_experiment.sh ...`. O CSV ganha as colunas `cpu_media_pct` e `mem_usada_max_mb`, e os dados por segundo ficam em `<cenario>/c<N>-recursos.csv`.
- **Rodando o `hey` no host e o app na VM:** rode `./experiments/monitor.sh recursos.csv` na VM durante o teste e guarde o arquivo junto dos resultados.

Sem `MONITOR=1` (ou sem o `monitor.sh` rodando na VM), as colunas `cpu_media_pct` e `mem_usada_max_mb` ficam vazias, e sem elas não dá para saber qual recurso saturou. Rode um cenário (configuração da VM) de cada vez, usando o nome do cenário para identificar a pasta. Os resultados são ignorados pelo git (`experiments/results/`); se quiser versioná-los no repositório da atividade, remova essa linha do `.gitignore`.

## Parâmetros para os experimentos

| O que variar | Como | Efeito esperado |
|--------------|------|-----------------|
| Demanda | `-c` (concorrência) do gerador de carga | Mais memória em uso e mais disputa pela largura de banda. O tempo de resposta sobe. |
| Custo por requisição | `size_mb` e `passes` | Mais tempo por requisição e mais RAM por requisição. |
| Memória da VM | Configuração do VirtualBox | Com pouca RAM há swap, o tempo de resposta degrada e pode ocorrer OOM. |
| CPUs da VM / `--workers` | Configuração do VirtualBox e flag do uvicorn | Mais paralelismo, até saturar a largura de banda da memória. |

## Estrutura do projeto

```
memory-app/
├── main.py            # aplicação FastAPI
├── requirements.txt   # dependências
├── postman/           # collection Postman e script Newman
├── experiments/       # scripts do hey e de monitoramento de recursos
├── README.md          # este arquivo
└── .gitignore
```
