from tqdm import tqdm
from weaviate import Client
import os
import requests
import json
import logging
import runpod

from goldenverba.components.interfaces import Embedder
from goldenverba.components.document import Document


class OllamaEmbedder(Embedder):

    def __init__(self):
        super().__init__()
        self.name = "OllamaEmbedder"
        self.requires_env = ["OLLAMA_URL", "OLLAMA_MODEL"]
        self.description = "Embeds and retrieves objects using Ollama and the model specified in the environment variable 'OLLAMA_MODEL'"
        self.vectorizer = "OLLAMA"
        self.url = os.environ.get("OLLAMA_URL", "")
        self.model = os.environ.get("OLLAMA_MODEL", "")
        self.endpoint = os.environ.get("RUNPOD_ENDPOINT", "")

        logging.basicConfig(level=logging.DEBUG)
        runpod.api_key = os.environ.get("RUNPOD_API_KEY","")



    def embed(
        self,
        documents: list[Document],
        client: Client,
        logging: list[dict],
    ) -> bool:
        """Embed verba documents and its chunks to Weaviate
        @parameter: documents : list[Document] - List of Verba documents
        @parameter: client : Client - Weaviate Client
        @parameter: batch_size : int - Batch Size of Input
        @returns bool - Bool whether the embedding what successful.
        """
        for document in tqdm(
            documents, total=len(documents), desc="Vectorizing document chunks"
        ):
            for chunk in tqdm(document.chunks, total=len(document.chunks), desc="Vectorizing Chunks"):
                chunk.set_vector(self.vectorize_chunk(document.name + " : " + chunk.text))

        return self.import_data(documents, client, logging)

    def vectorize_chunk(self, chunk) -> list[float]:
        try:
            embeddings = []
            # embedding_url = self.url + "/api/embeddings"
            # data = {"model": self.model, "prompt": chunk}

            #new format for runpod ollama
            print(f'chunks {chunk}')
            data = {
                    "input": {
                        "method_name": "api/embeddings",
                        "input": {
                        "prompt": chunk
                        }
                    }
                    }
            
            endpoint = runpod.Endpoint(self.endpoint)
            response = endpoint.run_sync(data,timeout=120)


            # response = requests.post(url, json=data, headers=headers)
            # print(response)
            # print(f'response from ollama embedder: {response}')
            embeddings = response.get("embedding", [])
            return embeddings

        except Exception:
            raise

    def vectorize_query(self, query: str) -> list[float]:
        return self.vectorize_chunk(query)
