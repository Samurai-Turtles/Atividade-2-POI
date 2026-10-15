import random
from locust import HttpUser, events, task


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--endpoint",
        type=str,
        default="/io/simple",
        help="Rota a ser testada (/io/simple ou /io/complex)",
    )
    parser.add_argument(
        "--espera-min",
        type=float,
        default=0.0,
        help="Pausa mínima entre requisições",
    )
    parser.add_argument(
        "--espera-max",
        type=float,
        default=0.0,
        help="Pausa máxima entre requisições",
    )


class UsuarioIO(HttpUser):
    def wait_time(self):
        opcoes = self.environment.parsed_options
        return random.uniform(opcoes.espera_min, opcoes.espera_max)

    @task
    def executar_io(self):
        endpoint = self.environment.parsed_options.endpoint
        self.client.get(endpoint, name=endpoint)