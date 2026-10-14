"""Gera os gráficos comparativos a partir de results/*/resultados.csv.

Uso: python plot.py [cenario1 cenario2 ...]   (padrão: todos em results/)
Saída: results/graficos/*.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

base = Path(__file__).parent / "results"
nomes = sys.argv[1:] or sorted(p.name for p in base.iterdir() if (p / "resultados.csv").exists())
dfs = {n: pd.read_csv(base / n / "resultados.csv") for n in nomes}
saida = base / "graficos"
saida.mkdir(exist_ok=True)

graficos = [
    ("req_por_s", "Vazão (req/s)", "vazao.png", "Vazão x concorrência"),
    ("p50_s", "Latência P50 (s)", "latencia_p50.png", "Latência mediana x concorrência"),
    ("p95_s", "Latência P95 (s)", "latencia_p95.png", "Latência P95 x concorrência"),
    ("cpu_media_pct", "CPU média da VM (%)", "cpu.png", "Uso de CPU x concorrência"),
    ("mem_usada_max_mb", "Memória usada máx. na VM (MB)", "memoria.png", "Uso de memória x concorrência"),
    ("swap_max_mb", "Swap usado máx. na VM (MB)", "swap.png", "Uso de swap x concorrência"),
    ("erros", "Erros (conexão/timeout)", "erros.png", "Erros x concorrência"),
]

for col, rotulo, arq, titulo in graficos:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for nome, df in dfs.items():
        if col in df and df[col].notna().any():
            ax.plot(df["concorrencia"], df[col], marker="o", label=nome)
    ax.set_xlabel("Concorrência (conexões simultâneas)")
    ax.set_ylabel(rotulo)
    ax.set_title(titulo)
    ax.set_xticks(sorted({c for df in dfs.values() for c in df["concorrencia"]}))
    ax.grid(alpha=0.3)
    ax.legend(title="Cenário")
    fig.tight_layout()
    fig.savefig(saida / arq, dpi=150)
    plt.close(fig)

# tabela resumo para colar no relatório
resumo = pd.concat(dfs.values())[[
    "cenario", "concorrencia", "req_por_s", "media_s", "p95_s", "respostas_200",
    "erros", "cpu_media_pct", "mem_usada_max_mb", "swap_max_mb"
]]
resumo.to_csv(saida / "resumo.csv", index=False)
print(f"Gráficos e resumo em {saida}")
