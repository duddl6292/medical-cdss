FROM mosecorg/mosec:0.9.7

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY inference/mosec/requirements.runtime.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY inference/mosec/app /workspace/app

EXPOSE 8000

CMD ["python", \
    "/workspace/app/server.py", \
    "--address", \
    "0.0.0.0", \
    "--port", \
    "8000", \
    "--timeout", \
    "300000"]