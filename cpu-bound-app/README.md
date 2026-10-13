# cpu-bound-app

API web (apenas backend) em Python com perfil **CPU-bound**, usada em experimentos de desempenho com variação de demanda e de recursos computacionais.

Cada requisição gera duas matrizes quadradas N x N de forma determinística e as multiplica em Python puro, com três laços aninhados (O(n³)). Não há disco, banco de dados, rede nem cache: todo o custo da requisição é processamento, e o tamanho da matriz controla a carga. A resposta traz apenas um resumo do resultado, para que serialização e rede não pesem no tempo medido.

## Rota

`GET /matriz?tamanho=<int>`

| Parâmetro | Obrigatório | Padrão | Descrição |
|-----------|-------------|--------|-----------|
| `tamanho` | não | 200 | Dimensão N das matrizes, inteiro entre 1 e `TAMANHO_MAXIMO` |

Exemplo:

```bash
curl "http://localhost:8000/matriz?tamanho=3"
```

```json
{"soma": 639, "tamanho": 3, "traco": 201}
```

- `traco`: soma da diagonal principal da matriz resultante.
- `soma`: soma de todos os elementos da matriz resultante.

Valores inválidos retornam `400`:

```json
{"erro": "O parâmetro 'tamanho' deve estar entre 1 e 500."}
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `PORT` | 8000 | Porta HTTP |
| `WEB_CONCURRENCY` | 1 | Número de workers (processos) do Uvicorn |
| `TAMANHO_MAXIMO` | 500 | Maior valor aceito para `tamanho` |

## Estrutura

```
.
├── src/
│   ├── app.py        # rota e multiplicação de matrizes
│   └── schema.py     # validação do parâmetro tamanho
├── Dockerfile
├── Makefile
└── requirements.txt
```

## Executar localmente

Com um ambiente Python ativado (venv ou conda):

```bash
make install
make run
```

As variáveis podem ser passadas ao `make`, por exemplo `make run WEB_CONCURRENCY=4 PORT=8080`.

## Executar com Docker

```bash
make docker-build
make docker-run WEB_CONCURRENCY=2
make docker-stop
```

Sem o Makefile:

```bash
docker build -t cpu-bound-app .
docker run --rm -p 8000:8000 -e WEB_CONCURRENCY=2 cpu-bound-app
```

Para limitar os recursos do contêiner nos experimentos, use por exemplo `--cpus=1 --memory=256m` no `docker run`.

## Observações

- A aplicação usa FastAPI servido pelo Uvicorn. Os workers são processos, porque o GIL impede que threads executem código Python em paralelo; o paralelismo vem do número de workers.
- A rota é `async def` de propósito: o cálculo bloqueia o event loop, então cada worker atende uma requisição por vez. Com `def`, o FastAPI executaria as requisições num pool de threads que disputam o GIL, o que reduz a vazão e deixa a latência irregular.
- Ajuste `WEB_CONCURRENCY` conforme o número de CPUs disponíveis: mais workers do que CPUs não aumenta a vazão, apenas divide o tempo de CPU entre eles.
- Como referência, `tamanho=500` leva alguns segundos por requisição em um núcleo.
- O log de acesso por requisição do Uvicorn é desativado (`--no-access-log`) para não somar custo de I/O às medições.
