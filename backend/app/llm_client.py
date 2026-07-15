"""
LLM Client for interacting with OpenRouter API.
Supports GPT-4.1 Mini (default), Gemini, and Claude models.
"""
import json
import time
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings


class LLMClient:
    """
    Client for making LLM calls via OpenRouter API.
    Supports multiple model providers with a unified interface.
    """

    def __init__(self, model: Optional[str] = None):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = model or settings.LLM_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Lead Qualification Agent",
        }

    def _build_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Build the messages array for the LLM call."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a call to the LLM via OpenRouter.

        Args:
            system_prompt: System-level instructions for the model
            user_prompt: User input/question
            temperature: Controls randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            response_format: Optional format specification (e.g., {"type": "json_object"})

        Returns:
            Parsed response dictionary with 'content' and 'usage' keys
        """
        messages = self._build_messages(system_prompt, user_prompt)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

                return {
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                    "model": result.get("model", self.model),
                    "success": True,
                }
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except Exception:
                error_detail = str(e)
            return {
                "content": None,
                "usage": {},
                "model": self.model,
                "success": False,
                "error": f"HTTP {e.response.status_code}: {error_detail}",
            }
        except Exception as e:
            return {
                "content": None,
                "usage": {},
                "model": self.model,
                "success": False,
                "error": str(e),
            }

    def call_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Make an LLM call and parse the response as JSON.

        Returns:
            Dictionary with 'parsed' (the JSON object), 'raw', and 'success' keys
        """
        result = self.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        if not result["success"]:
            return {
                "parsed": None,
                "raw": result.get("error", "Unknown error"),
                "success": False,
                "error": result.get("error"),
            }

        content = result["content"]
        try:
            # Try to parse as JSON directly
            parsed = json.loads(content)
            return {
                "parsed": parsed,
                "raw": content,
                "success": True,
                "usage": result.get("usage", {}),
            }
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    return {
                        "parsed": None,
                        "raw": content,
                        "success": False,
                        "error": "Response was not valid JSON",
                    }
                parsed = json.loads(json_str)
                return {
                    "parsed": parsed,
                    "raw": content,
                    "success": True,
                    "usage": result.get("usage", {}),
                }
            except (json.JSONDecodeError, IndexError):
                return {
                    "parsed": None,
                    "raw": content,
                    "success": False,
                    "error": "Response was not valid JSON",
                }