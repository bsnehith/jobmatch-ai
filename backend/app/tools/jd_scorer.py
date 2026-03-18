import json
import re
from typing import Any, Dict, List

from langchain_google_genai import ChatGoogleGenerativeAI


class JDScorerTool:
    def __init__(self, *, model: str, api_key: str, temperature: float = 0.2):
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )

    @staticmethod
    def _extract_json(payload: str) -> Dict[str, Any]:
        match = re.search(r"\{.*\}", payload, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

    def run(self, *, candidate: str, profile: str, jd: str, command: str = "") -> Dict[str, Any]:
        prompt = f"""
You are an ATS hiring evaluator.
Return only strict JSON with keys:
- score: integer 0-100
- strengths: array with exactly 3 short points
- gaps: array with exactly 2 short points
- recommendation: one of "Interview", "No-Hire", "Insufficient Info — Request Resume"
- reason: one concise sentence

Rules:
- If profile is weak or missing, score should be 40-55 and recommendation should usually be "Insufficient Info — Request Resume".
- Never give 0 score only because profile is missing.
- If command mentions explicit skills, use them in scoring.
- If candidate is clearly wrong domain, score below 30 and "No-Hire".

Candidate: {candidate}
Recruiter command: {command}
Profile evidence: {profile}
Job description: {jd}
"""
        raw = self.llm.invoke(prompt)
        parsed = self._extract_json(str(raw.content))

        if not parsed:
            return {
                "score": 50,
                "strengths": [
                    "Role keywords partially match",
                    "Some relevant technical background",
                    "Potential to qualify with more evidence",
                ],
                "gaps": [
                    "Insufficient verified project depth",
                    "Missing deployment/cloud proof",
                ],
                "recommendation": "Insufficient Info — Request Resume",
                "reason": "Public profile data is not enough for a confident hiring decision.",
            }

        score = max(0, min(100, int(parsed.get("score", 50))))
        strengths: List[str] = parsed.get("strengths", [])[:3]
        gaps: List[str] = parsed.get("gaps", [])[:2]

        while len(strengths) < 3:
            strengths.append("Relevant profile signal")
        while len(gaps) < 2:
            gaps.append("More evidence required")

        return {
            "score": score,
            "strengths": strengths,
            "gaps": gaps,
            "recommendation": parsed.get(
                "recommendation", "Insufficient Info — Request Resume"
            ),
            "reason": parsed.get(
                "reason", "Decision generated from available evidence."
            ),
        }
