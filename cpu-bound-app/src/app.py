from fastapi import FastAPI
from fastapi.responses import JSONResponse

from schema import validar_tamanho

app = FastAPI()


def gerar_matriz(n, deslocamento):
    """Gera uma matriz n x n determinística a partir dos índices."""
    return [[(i * n + j + deslocamento) % 10 for j in range(n)] for i in range(n)]


def multiplicar(a, b):
    """Multiplicação clássica O(n³) em Python puro."""
    n = len(a)
    resultado = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            acumulado = 0
            for k in range(n):
                acumulado += a[i][k] * b[k][j]
            resultado[i][j] = acumulado
    return resultado


@app.get("/matriz")
async def matriz(tamanho: str | None = None):
    tamanho, erro = validar_tamanho(tamanho)
    if erro:
        return JSONResponse({"erro": erro}, status_code=400)

    produto = multiplicar(gerar_matriz(tamanho, 1), gerar_matriz(tamanho, 3))
    return {
        "tamanho": tamanho,
        "traco": sum(produto[i][i] for i in range(tamanho)),
        "soma": sum(sum(linha) for linha in produto),
    }
