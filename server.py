from mosec import Server, Worker


class TestWorker(Worker):
    def forward(self, data):
        return {
            "status": "ok",
            "service": "medical-mosec",
            "received": data,
        }


if __name__ == "__main__":
    server = Server()
    server.append_worker(TestWorker, num=1)
    server.run()