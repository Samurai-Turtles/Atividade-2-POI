# IO-Bound API

API desenvolvida para a atividade prática de avaliação de desempenho, demanda e provisionamento de recursos em Máquinas Virtuais (usando, por exemplo, o VirtualBox).

Esta aplicação possui perfil **IO-bound** real de disco: as requisições gravam e leem arquivos temporários forçando a descarga física no disco com `os.fsync()`. 

O arquivo é excluído imediatamente após o uso para não ocupar espaço de armazenamento desnecessário na VM, além de retirar a variável de disco (quase) cheio como fator de ruído nos testes, o que evita a degradação de desempenho causada pela fragmentação do sistema de arquivos e pela sobrecarga do alocador ao buscar blocos livres contíguos. Fugindo do escopo do IO puro, garantindo que o gargalo medido seja puramente decorrente da concorrência e do provisionamento da máquina virtual.

---

## 1. Estrutura dos Arquivos

```text
.
├── Dockerfile
├── README.md
├── main.py
└── requirements.txt
```

---

## 2. Execução Local ou na VM (Sem Docker)

### Pré-requisitos
* Python 3.10+
* `pip` e `venv`

### Passo a passo
1. Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o servidor:
   * **Execução direta via Python:**
     ```bash
     python main.py
     ```
   * **Ou via Uvicorn:**
     ```bash
     uvicorn main:app --host 0.0.0.0 --port 8095
     ```

A API estará acessível em `http://localhost:8095`.

---

## 3. Execução com Docker

1. **Construir a imagem:**
   ```bash
   docker build -t io-bound-app .
   ```

2. **Executar o container:**
   ```bash
   docker run -d --name io-app -p 8095:8095 io-bound-app
   ```

---

## 4. Endpoints da API

* **`GET /`**: Checagem de conectividade básica.
  ```bash
  curl http://localhost:8095/
  ```

* **`GET /io/simple`**:
  * Escreve 5 MB sequenciais (blocos de 1 MB).
  * Executa 1 `fsync` único para persistir no disco.
  * Lê o arquivo de volta e remove do disco.
  ```bash
  curl http://localhost:8095/io/simple
  ```

* **`GET /io/complex`**:
  * Escreve 10 MB fragmentados (blocos de 64 KB).
  * Executa 5 chamadas de `fsync` intercaladas durante a escrita para estressar IOPS (sem o fsync, o kernel só escreveria na memória e só no final escreveria no disco, com este eu forço a escrita no disco).
  * Lê o arquivo de volta e remove do disco.
  ```bash
  curl http://localhost:8095/io/complex
  ```

---

## 5. Monitoramento Durante os Experimentos na VM

Para acompanhar o comportamento do disco e da CPU na VM enquanto ferramentas de carga (como Locust, k6, ab ou wrk) executam:

```bash
# Monitora tempo de espera de I/O (%wa) e blocos lidos/escritos a cada 1s:
vmstat 1

# Monitora IOPS e taxa de ocupação do disco (%util) a cada 1s:
iostat -xz 1
```