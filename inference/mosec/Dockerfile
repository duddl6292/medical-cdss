FROM python:3.12-slim

ARG TORCH_VERSION=2.11.0
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu126

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace

WORKDIR /workspace

COPY inference/mosec/requirements.runtime.txt /tmp/requirements.txt

# PyTorch 2.11.0 CUDA 12.6 공식 wheel을 먼저 설치한다.
RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --index-url "${TORCH_INDEX_URL}" \
        "torch==${TORCH_VERSION}" \
    && python -m pip install -r /tmp/requirements.txt \
    && python -m pip check \
    && python -c "import torch; \
assert torch.__version__.split('+')[0] == '${TORCH_VERSION}', torch.__version__; \
assert torch.version.cuda == '12.6', torch.version.cuda"

COPY inference/app /workspace/app

EXPOSE 8000

CMD ["sh", "-c", "exec python -m app.server --address 0.0.0.0 --port \"${PORT:-8000}\" --timeout \"${MOSEC_TIMEOUT_MS:-300000}\""]