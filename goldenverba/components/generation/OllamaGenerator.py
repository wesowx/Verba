import os
import json
import aiohttp
import runpod
from wasabi import msg

from typing import List, Dict, AsyncGenerator

from goldenverba.components.interfaces import Generator
from goldenverba.components.types import InputConfig


class OllamaGenerator(Generator):
    def __init__(self):
        super().__init__()
        self.name = "Ollama"
        self.url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.endpoint = os.environ.get("RUNPOD_OLLAMA_GENERATOR_ENDPOINT", "")
        runpod.api_key = os.environ.get("RUNPOD_API_KEY","")
        
        self.description = f"Generatoror model using generator model deployed in Ollama, check instance for model name"
        self.context_window = 10000

        # Fetch available models
        models = get_models(self.endpoint)

        # Configure the model selection dropdown
        self.config["Model"] = InputConfig(
            type="dropdown",
            value=models[0] if models else "",
            description=f"Select an installed Ollama model from {self.url}.",
            values=models,
        )

    async def generate_stream(
        self,
        config: Dict,
        query: str,
        context: str,
        conversation: List[Dict] = [],
    ) -> AsyncGenerator[Dict, None]:

        system_message = config.get("System Message").value
        messages = self._prepare_messages(query, context, conversation, system_message)

        try:
            data = {
                    "input": {
                        "method_name": "api/chat",
                        "input": {
                        "messages": messages
                        }
                    }
                    }
            
            print(f'payload: {data}')
            endpoint = runpod.Endpoint(self.endpoint)
            run_request = endpoint.run(data)
            # Initial check without blocking, useful for quick tasks
            status = run_request.status()
            print(f"Initial job status: {status}")

            if status != "COMPLETED":
                # Polling with timeout for long-running tasks
                output = run_request.output(timeout=60)
            else:
                output = run_request.output()
            print(f"Job output: {output}")
            for line in output.get("message").get("content"):
                if line.strip():  # Ensure line is not just whitespace
                    # json_data = json.loads(
                    #     line.decode("utf-8")
                    # )  # Decode bytes to string then to JSON
                    # output = json_data.get("output")
                    #updated to format from runpod ollama
                    message = output.get("message", {}).get("content", "")
                    finish_reason = (
                        "stop" if output.get("done", False) else ""
                    )

                    yield {
                        "message": message,
                        "finish_reason": finish_reason,
                    }
                else:
                    yield {
                        "message": "",
                        "finish_reason": "stop",
                    }

                return

        except Exception as e:
            yield self._error_response(
                f"Unexpected error, make sure to have ollame model installed: {str(e)}"
            )

    def _prepare_messages(
        self,
        query: str,
        context: str,
        conversation: List[Dict],
        system_message: str,
    ) -> List[Dict]:
        """Prepare the message list for the Ollama API request."""
        messages = [
            {"role": "system", "content": system_message},
            *[
                {"role": message.type, "content": message.content}
                for message in conversation
            ],
            {
                "role": "user",
                "content": f"With this provided context: {context} Please answer this query: {query}",
            },
        ]
        return messages

    @staticmethod
    def _process_response(line: bytes) -> Dict:
        """Process a single line of response from the Ollama API."""
        json_data = json.loads(line.decode("utf-8"))

        if "error" in json_data:
            return {
                "message": json_data.get("error", "Unexpected Error"),
                "finish_reason": "stop",
            }

        return {
            "message": json_data.get("message", {}).get("content", ""),
            "finish_reason": "stop" if json_data.get("done", False) else "",
        }

    @staticmethod
    def _empty_response() -> Dict:
        """Return an empty response."""
        return {"message": "", "finish_reason": "stop"}

    @staticmethod
    def _error_response(message: str) -> Dict:
        """Return an error response."""
        return {"message": message, "finish_reason": "stop"}



def get_models(endpoint: str):
    try:
        input_payload = {
            "input": {
                "method_name": "api/generate",
                "input": {
                    "prompt": "test"
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