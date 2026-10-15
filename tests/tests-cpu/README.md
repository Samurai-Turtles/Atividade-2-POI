# Testes de carga com Locust

Testes de carga da `cpu-bound-app` com o [Locust](https://locust.io). O objetivo é observar como vazão e tempo de resposta variam com a demanda (número de usuários e tamanho da matriz) e com os recursos da VM (CPUs e `WEB_CONCURRENCY`).

## Estrutura

```
tests/
├── locustfile.py          # usuário que chama GET /matriz
├── locust.conf            # endereço da aplicação (alvo)
├── cenarios/
│   ├── baixa-demanda.conf
│   └── alta-demanda.conf
├── relatorios/            # relatórios gerados (HTML e CSV)
└── requirements.txt
```

O `locustfile.py` define um único tipo de usuário. O que muda entre os cenários (tamanho da matriz, pausa entre requisições, número de usuários e duração) fica nos arquivos de `cenarios/`.

## Configuração do alvo

O endereço da aplicação fica em `locust.conf`:

```ini
host = http://localhost:8000
```

Com a aplicação na VM do VirtualBox, o endereço depende do modo de rede da VM:

- **NAT com redirecionamento de porta** (Configurações → Rede → Avançado → Redirecionamento de portas, ex.: porta 8000 do hospedeiro para a 8000 da VM): `http://localhost:8000`.
- **Placa em modo host-only ou em ponte:** `http://<IP da VM>:8000`. O IP aparece com `ip addr` dentro da VM; em host-only costuma ser algo como `192.168.56.x`.

Antes de rodar os testes, confirme o acesso com `curl "http://<alvo>/matriz?tamanho=3"`. Também é possível trocar o alvo sem editar o arquivo, com `make teste-baixa ALVO=http://192.168.56.10:8000`.

## Cenários

| Parâmetro | Baixa demanda | Alta demanda |
|---|---|---|
| Usuários simultâneos | 5 | 20 |
| Entrada de usuários | 1 por segundo | 1 a cada 5 s (rampa de ~100 s) |
| `tamanho` da matriz | 100 | 500 |
| Pausa entre requisições | 1 a 3 s (aleatória) | nenhuma |
| Duração | 3 min | 5 min |

### Baixa demanda

Representa um uso leve: poucos usuários, matrizes pequenas (~40 ms de CPU por requisição) e uma pausa entre as requisições de cada usuário. São cerca de 2,5 req/s, o que ocupa uma fração pequena de um núcleo. O resultado esperado é latência estável e próxima do tempo de cálculo, sem fila. Esse cenário serve de linha de base para comparação.

### Alta demanda

Busca o maior consumo de CPU possível. Como a aplicação é CPU-bound e cada worker atende uma requisição por vez, o consumo máximo acontece quando **todos os workers ficam ocupados o tempo todo**. Para isso, o cenário usa:

- matriz de tamanho 500 (alguns segundos de CPU por requisição);
- nenhuma pausa: cada usuário envia uma nova requisição assim que recebe a resposta;
- mais usuários do que workers, para que sempre haja requisições na fila.

O resultado esperado é a CPU da VM em ~100% em todos os núcleos usados pelos workers. A vazão para de crescer quando os usuários passam do número de workers, e o tempo de resposta cresce com a fila. A rampa de usuários deixa esse ponto de saturação visível nos gráficos.

O cenário não usa o tamanho máximo aceito pela aplicação (`TAMANHO_MAXIMO`), porque o consumo de CPU já é de 100% com 500. Uma matriz de 1000 levaria ~8 vezes mais por requisição, e poucas requisições terminariam dentro do tempo do teste. Se a VM for lenta e mesmo assim terminarem poucas requisições, reduza `tamanho` em `alta-demanda.conf` (ex.: 300): o consumo continua máximo, com mais amostras.

## Como executar

A partir da pasta `cpu-bound-app/`, com um ambiente Python ativado:

```bash
make install-testes                 # instala o Locust

make teste-baixa
make teste-alta
```

Variáveis opcionais:

- `ALVO`: sobrescreve o endereço de `locust.conf`.
- `ROTULO`: identifica o experimento no nome dos relatórios, por exemplo a configuração da VM.

```bash
make teste-alta ALVO=http://192.168.56.10:8000 ROTULO=2cpus-2workers
```

Qualquer opção do Locust também pode ser sobrescrita por variável de ambiente, sem editar os cenários. Por exemplo, `LOCUST_RUN_TIME=1m make teste-alta`.

Sem o Makefile, de dentro de `tests/`:

```bash
locust --config cenarios/baixa-demanda.conf
```

Nesse caso os relatórios são salvos com nome fixo e sobrescritos a cada execução.

## Relatórios

Cada execução gera em `relatorios/` arquivos com o nome `<cenario>[_<rotulo>]_<data-hora>`:

- **`.html`**: relatório que abre no navegador, sem precisar de internet. Traz tabelas de estatísticas (requisições, falhas, tempo médio, mínimo, máximo e percentis) e três gráficos ao longo do tempo:
  - **Total Requests per Second**: vazão e falhas por segundo. Mostra o patamar de vazão da aplicação.
  - **Response Times (ms)**: mediana (p50) e percentil 95 do tempo de resposta. Mostra o crescimento da fila.
  - **Number of Users**: usuários simultâneos. Mostra a rampa de carga.
- **`_stats.csv`**: resumo final por requisição (contagem, falhas, tempos e percentis).
- **`_stats_history.csv`**: série temporal, linha a linha, de vazão, percentis e usuários. Serve para montar gráficos que comparem experimentos (ex.: 1, 2 e 4 workers no mesmo gráfico).
- **`_failures.csv`** e **`_exceptions.csv`**: erros ocorridos, se houver.

## Recomendações para os experimentos

- **Rode o Locust fora da VM**, no hospedeiro. Assim o gerador de carga não disputa CPU com a aplicação.
- **Varie um fator por vez:** número de CPUs da VM, `WEB_CONCURRENCY` ou cenário. Use `ROTULO` para registrar a combinação.
- **Mantenha `WEB_CONCURRENCY` igual ao número de CPUs da VM.** Mais workers do que CPUs não aumenta a vazão.
- **Ajuste o tamanho máximo na aplicação:** o `TAMANHO_MAXIMO` dela precisa ser maior ou igual ao `tamanho` do cenário, senão as requisições retornam 400 e aparecem como falhas.
- **Requisições em andamento no fim do teste não entram nas estatísticas.** No cenário de alta demanda, onde cada requisição pode levar vários segundos na fila, isso é esperado.
