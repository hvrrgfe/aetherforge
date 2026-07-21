"""Model Router - OpenAI-compatible API abstraction layer.

Supports any API that follows the OpenAI chat completions format.
"""
import json, time, threading, os
from typing import Optional, Dict, List, Any, Callable
from aetherforge.agents.errors import ModelRouterError
from aetherforge.agents.policies import TokenBudget

class ModelRouter:
    """Routes requests to an OpenAI-compatible API endpoint.

    Supports configurable endpoint, model name, API key, and token budget.
    """

    def __init__(self, endpoint: str = "", api_key: str = "", model_name: str = "", token_budget=None):
        self._endpoint = endpoint.rstrip("/") or os.environ.get("AETHERFORGE_ENDPOINT", "https://api.openai.com/v1")
        self._api_key = api_key or os.environ.get("AETHERFORGE_API_KEY", "")
        self._model_name = model_name or os.environ.get("AETHERFORGE_MODEL", "gpt-4")
        self._token_budget = token_budget or TokenBudget()
        self._last_response: Optional[Dict] = None
        self._call_count = 0

    def chat(self, messages: List[Dict], temperature: float = 0.7,
             max_tokens: int = 1024, stream: bool = False) -> Dict:
        """Send a chat completion request."""
        self._call_count += 1
        try:
            import urllib.request
            import urllib.error
            url = f"{self._endpoint}/chat/completions"
            body = json.dumps({
                "model": self._model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": min(max_tokens, self._token_budget.remaining),
                "stream": stream,
            }).encode("utf-8")
            req = urllib.request.Request(url, data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
                method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except ImportError:
            # Fallback: try requests library
            try:
                import requests as req_lib
                resp = req_lib.post(
                    f"{self._endpoint}/chat/completions",
                    json={"model": self._model_name, "messages": messages,
                          "temperature": temperature,
                          "max_tokens": min(max_tokens, self._token_budget.remaining),
                          "stream": stream},
                    headers={"Content-Type": "application/json",
                             "Authorization": f"Bearer {self._api_key}"},
                    timeout=30,
                )
                result = resp.json()
            except ImportError:
                raise ModelRouterError("No HTTP library available (need urllib or requests)")
            except Exception as e:
                raise ModelRouterError(f"HTTP request failed: {e}")
        except urllib.error.HTTPError as e:
            raise ModelRouterError(f"API error {e.code}: {e.read().decode('utf-8')[:200]}")
        except Exception as e:
            raise ModelRouterError(f"Request failed: {e}")

        self._last_response = result
        # Track token usage
        usage = result.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        self._token_budget.use(total_tokens)

        return result

    def extract_content(self, response: Dict) -> str:
        """Extract text content from API response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def extract_json(self, response: Dict) -> Optional[Dict]:
        """Extract and parse JSON from response content."""
        content = self.extract_content(response)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    @property
    def budget(self) -> TokenBudget:
        return self._token_budget

    def to_dict(self) -> dict:
        return {
            "endpoint": self._endpoint,
            "model": self._model_name,
            "call_count": self._call_count,
            "budget": self._token_budget.to_dict(),
        }