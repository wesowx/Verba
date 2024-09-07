import os
import requests
from wasabi import msg
import runpod

from goldenverba.components.interfaces import Embedding
from goldenverba.components.types import InputConfig
from goldenverba.components.util import get_environment


class OllamaEmbedder(Embedding):

    def __init__(self):
        super().__init__()
        self.name = "Ollama"
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.endpoint = os.environ.get("RUNPOD_OLLAMA_EMBEDDER_ENDPOINT", "")
        runpod.api_key = os.environ.get("RUNPOD_API_KEY","")

        self.description = f"Vectorizes documents and queries using Ollama."
        models = get_models(self.endpoint)

        self.config = {
            "Model": InputConfig(
                type="dropdown",
                value=models[0],
                description=f"Select a installed Ollama model",
                values=models,
            ),
        }

    # async def vectorize(self, config: dict, content: list[str]) -> list[float]:

    #     model = config.get("Model").value

    #     data = {"model": model, "input": content}

    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(self.url + "/api/embed", json=data) as response:
    #             response.raise_for_status()
    #             data = await response.json()
    #             embeddings = data.get("embeddings", [])
    #             return embeddings
            

    async def vectorize(self, config: dict, content: list[str]) -> list[float]:
        # input_payload = {"input": {"prompt": "Hello, World!"}}
        input_payload = {
            "input": {
                "method_name": "api/embed",
                "input": {
                    "input": content
                }
            }
        }
        try:
            endpoint = runpod.Endpoint(self.endpoint)
            run_request = endpoint.run(input_payload)

            # Initial check without blocking, useful for quick tasks
            status = run_request.status()
            print(f"Initial job status: {status}")

            if status != "COMPLETED":
                # Polling with timeout for long-running tasks
                output = run_request.output(timeout=60)
            else:
                output = run_request.output()
            # print(f"Job output: {output}")
            # print("embeddings", output.get("embeddings"))
            return output.get("embeddings", [])
        except Exception as e:
            print(f"An error occurred: {e}")

def get_models(endpoint: str):
    try:
        input_payload = {
            "input": {
                "method_name": "api/embed",
                "input": {
                    "input": "test"
                }
            }
        }
        
        endpoint = runpod.Endpoint(endpoint)
        response = endpoint.run_sync(input_payload,timeout=120)
        model = response.get("model", "")
        print("model", model)
        return [model]
    except Exception as e:
        msg.info(f"Couldn't connect to Ollama")
        return [f"Couldn't connect to Ollama"]
