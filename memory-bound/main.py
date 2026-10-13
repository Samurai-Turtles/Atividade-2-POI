"""Backend memory-bound.

Cada requisição aloca um buffer de `size_mb` MB, preenche e faz acessos
aleatórios (gather) sobre ele. O buffer é maior que o cache da CPU, então o
tempo é dominado pelo acesso à memória, e o consumo de RAM cresce com a
concorrência (N requisições simultâneas ~ N * size_mb MB).
"""
import time

import numpy as np
from fastapi import FastAPI, Query

app = FastAPI(title="memory-bound")

rng = np.random.default_rng(42)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/memory")
def memory(
    size_mb: int = Query(64, ge=1, le=2048, description="tamanho do buffer em MB"),
    passes: int = Query(1, ge=1, le=100, description="número de passadas de acesso aleatório"),
):
    start = time.perf_counter()
    n = size_mb * 1024 * 1024 // 8
    buf = np.arange(n, dtype=np.int64)  # aloca e escreve todas as páginas
    total = 0
    for _ in range(passes):
        idx = rng.integers(0, n, size=n // 4)  # acessos aleatórios -> cache miss
        total += int(buf[idx].sum())
    elapsed = time.perf_counter() - start
    return {
        "size_mb": size_mb,
        "passes": passes,
        "checksum": total,
        "elapsed_ms": round(elapsed * 1000, 2),
    }
