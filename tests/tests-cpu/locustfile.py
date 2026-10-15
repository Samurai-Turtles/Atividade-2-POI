import random

from locust import HttpUser, events, task


@events.init_command_line_parser.add_listener
def _(parser):
    # Parâmetros dos cenários, definidos nos arquivos de cenarios/*.conf
    parser.add_argument("--tamanho", type=int, default=200, help="Dimensão N das matrizes")
    parser.add_argument("--espera-min", type=float, default=0, help="Pausa mínima entre requisições (s)")
    parser.add_argument("--espera-max", type=float, default=0, help="Pausa máxima entre requisições (s)")


class UsuarioMatriz(HttpUser):
    def wait_time(self):
        opcoes = self.environment.parsed_options
        return random.uniform(opcoes.espera_min, opcoes.espera_max)

    @task
    def multiplicar_matrizes(self):
        tamanho = self.environment.parsed_options.tamanho
        self.client.get("/matriz", params={"tamanho": tamanho}, name=f"/matriz?tamanho={tamanho}")
