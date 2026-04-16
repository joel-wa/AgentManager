"""
Focused checks for Gemini client compatibility with existing Ollama interface.
"""

from gemini_client import GeminiClient
from ollama_client import OllamaClient


def main():
    content = """```json
{
  "tool_calls": [
    {
      "name": "search",
      "arguments": {"query": "agent"}
    }
  ]
}
```"""

    gemini = GeminiClient(model="gemini-test")
    gemini_calls = gemini._parse_tool_calls(content, ["search", "read_file"])
    assert gemini_calls is not None
    assert len(gemini_calls) == 1
    assert gemini_calls[0]["name"] == "search"
    assert gemini_calls[0]["arguments"]["query"] == "agent"

    compatibility_client = OllamaClient(model="gemini-test")
    compat_calls = compatibility_client._parse_tool_calls(content, ["search"])
    assert compat_calls is not None
    assert len(compat_calls) == 1
    assert compat_calls[0]["name"] == "search"

    print("Gemini client compatibility checks passed")


if __name__ == "__main__":
    main()
