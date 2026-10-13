import os

TAMANHO_PADRAO = 200
TAMANHO_MAXIMO = int(os.environ.get("TAMANHO_MAXIMO", "1000"))


def validar_tamanho(valor):
    """Converte e valida o parâmetro `tamanho`. Retorna (tamanho, erro)."""
    if valor is None:
        return TAMANHO_PADRAO, None
    try:
        tamanho = int(valor)
    except ValueError:
        return None, "O parâmetro 'tamanho' deve ser um número inteiro."
    if not 1 <= tamanho <= TAMANHO_MAXIMO:
        return None, f"O parâmetro 'tamanho' deve estar entre 1 e {TAMANHO_MAXIMO}."
    return tamanho, None
