from typing import Any, Dict, List

from tavily import TavilyClient


class WebSearchTool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = TavilyClient(api_key=api_key) if api_key else None

    def run(self, query: str) -> Dict[str, Any]:
        if not query.strip():
            return {"found": False, "summary": "Empty query.", "results": []}

        if not self.client:
            return {
                "found": False,
                "summary": "TAVILY_API_KEY not configured. Live profile search unavailable.",
                "results": [],
            }

        response = self.client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        results: List[Dict[str, Any]] = response.get("results", [])
        answer = response.get("answer", "")

        if not results:
            return {
                "found": False,
                "summary": "No relevant public profile found for this candidate.",
                "results": [],
            }

        best_url = results[0].get("url", "")
        best_snippet = (results[0].get("content", "") or "")[:500]
        summary = answer or best_snippet or "Candidate profile evidence found."

        return {
            "found": True,
            "best_url": best_url,
            "summary": summary,
            "results": [
                {"title": item.get("title", ""), "url": item.get("url", "")}
                for item in results[:5]
            ],
        }
