FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

COPY inference/gateway/requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/requirements.txt \
    && python -m pip check

COPY inference/gateway/app /workspace/app

EXPOSE 8001

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8001}\" --proxy-headers"]
