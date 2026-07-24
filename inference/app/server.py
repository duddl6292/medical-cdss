from mosec import Server, Worker


class MockInferenceWorker(Worker):
    def forward(self, data):
        return {
            "status": "completed",
            "prediction": {
                "mask_uri": None,
                "preview_uri": None,
                "lesion_voxels": 0,
                "lesion_volume_ml": 0.0,
                "shape": [512, 512, 32],
                "spacing": [0.488281, 0.488281, 5.093584],
                "preview_slice_index": 16,
            },
            "timing": {
                "preprocessing_seconds": 0.0,
                "inference_seconds": 0.0,
                "postprocessing_seconds": 0.0,
                "total_seconds": 0.0,
            },
            "error": None,
        }


if __name__ == "__main__":
    server = Server()
    server.append_worker(MockInferenceWorker, num=1)
    server.run()