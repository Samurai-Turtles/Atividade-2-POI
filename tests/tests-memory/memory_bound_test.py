"""Teste de stress da memory-bound com o Locust, rodando no host (fora da VM).

A partir desta pasta (tests-memory/).

Interface web (http://localhost:8089):
    locust -f memory_bound_test.py

Sem interface, um cenário completo com relatório:
    locust -f memory_bound_test.py --headless \
        --csv relatorios/mem-3cpu-1gb --html relatorios/mem-3cpu-1gb.html

A carga sobe em degraus (STEPS usuários simultâneos, STEP_SECONDS cada) e o teste termina sozinho.
Não combine com -t. Cada usuário dispara requisições em sequência, sem pausa, então
N usuários = N requisições simultâneas = cerca de N x SIZE_MB de RAM na VM.

Variáveis: VM_URL (http://localhost), APP_PORT (8000), SIZE_MB (128), PASSES (3),
STEPS ("1 2 4 8 16 32"), STEP_SECONDS (60), REQUEST_TIMEOUT (30).
"""
import os

from locust import HttpUser, LoadTestShape, constant, task

SIZE_MB = int(os.getenv("SIZE_MB", "128"))
PASSES = int(os.getenv("PASSES", "3"))
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
NIVEIS = [int(n) for n in os.getenv("STEPS", "1 2 4 8 16 32").split()]
SEGUNDOS = int(os.getenv("STEP_SECONDS", "60"))


class MemoryUser(HttpUser):
    host = f"{os.getenv('VM_URL', 'http://localhost')}:{os.getenv('APP_PORT', '8000')}"
    wait_time = constant(0)

    @task
    def memory(self):
        self.client.get(
            f"/memory?size_mb={SIZE_MB}&passes={PASSES}",
            name=f"/memory (size_mb={SIZE_MB})",
            timeout=TIMEOUT,
        )


class DegrausDeCarga(LoadTestShape):
    """Um nível de usuários por degrau; encerra depois do último."""

    def tick(self):
        degrau = int(self.get_run_time() // SEGUNDOS)
        if degrau >= len(NIVEIS):
            return None
        return NIVEIS[degrau], NIVEIS[degrau]
