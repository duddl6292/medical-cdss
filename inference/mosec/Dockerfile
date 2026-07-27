FROM python:3.12-slim

ARG TORCH_VERSION=2.11.0
ARG TORCHVISION_VERSION=0.26.0
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cu126

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/workspace

WORKDIR /workspace

COPY inference/mosec/requirements.runtime.txt /tmp/requirements.txt

# PyTorch 2.11.0 CUDA 12.6 공식 wheel을 먼저 설치한다.
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir \
        --index-url "${TORCH_INDEX_URL}" \
        "torch==${TORCH_VERSION}" \
        "torchvision==${TORCHVISION_VERSION}" \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -c "import torch, torchvision; \
assert torch.__version__ == '${TORCH_VERSION}+cu126', torch.__version__; \
assert torchvision.__version__ == '${TORCHVISION_VERSION}+cu126', torchvision.__version__; \
assert torch.version.cuda == '12.6', torch.version.cuda; \
assert hasattr(torch.ops.torchvision, 'nms'), 'torchvision::nms missing'"

COPY inference/app /workspace/app

EXPOSE 8000

CMD ["sh", "-c", "python -m app.prepare_model && exec python -m app.server --address \"${MOSEC_ADDRESS:-0.0.0.0}\" --port \"${PORT:-${MOSEC_PORT:-8000}}\" --timeout \"${MOSEC_TIMEOUT_MS:-300000}\""]