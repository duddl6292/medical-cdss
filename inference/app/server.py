"""MOSEC server entry point for Exp05 inference."""

from mosec import Server

from .worker import MosecInferenceWorker


if __name__ == "__main__":
    server = Server()
    server.append_worker(
        MosecInferenceWorker,
        num=1,
    )
    server.run()