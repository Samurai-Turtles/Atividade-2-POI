import os
import tempfile
import time
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "IO-bound API"}


@app.get("/io/simple")
async def io_simple():
    """
    I/O Simples:
    - Escrita total: 5 MB sequenciais (blocos de 1 MB).
    - Executa um único fsync para persistir os 5 MB no disco.
    - Lê o arquivo completo e o remove imediatamente para não encher o disco.
    """
    size_mb = 5  # Quantidade gravada: 5 MB
    start = time.perf_counter()
    fd, path = tempfile.mkstemp(prefix="simple_io_")

    try:
        block = b"X" * (1024 * 1024)  # 1 MB
        for _ in range(size_mb):
            os.write(fd, block)
        os.fsync(fd)
        os.close(fd)

        with open(path, "rb") as f:
            _ = f.read()
    finally:
        if os.path.exists(path):
            os.remove(path)

    elapsed = time.perf_counter() - start
    return {"endpoint": "simple", "written_mb": size_mb, "time_seconds": round(elapsed, 4)}


@app.get("/io/complex")
async def io_complex():
    """
    I/O Complexo:
    - Escrita total: 10 MB fragmentados (blocos de 64 KB).
    - Executa 5 fsyncs intercalados ao longo da escrita para estressar IOPS.
    - Lê o arquivo completo e o remove imediatamente para não encher o disco.
    """
    size_mb = 10  # Quantidade gravada: 10 MB
    start = time.perf_counter()
    fd, path = tempfile.mkstemp(prefix="complex_io_")

    try:
        chunk = b"Z" * (64 * 1024)  # 64 KB
        total_chunks = (size_mb * 1024) // 64  # 160 blocos
        sync_interval = total_chunks // 5  # fsync disparado a cada 2 MB

        for i in range(total_chunks):
            os.write(fd, chunk)
            if i % sync_interval == 0:
                os.fsync(fd)

        os.fsync(fd)
        os.close(fd)

        with open(path, "rb") as f:
            _ = f.read()
    finally:
        if os.path.exists(path):
            os.remove(path)

    elapsed = time.perf_counter() - start
    return {"endpoint": "complex", "written_mb": size_mb, "time_seconds": round(elapsed, 4)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)