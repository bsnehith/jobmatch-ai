from typing import Any, Dict

from app.services.sqlite_service import SQLiteService


class DBTool:
    def __init__(self, sqlite_service: SQLiteService):
        self.sqlite_service = sqlite_service

    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        action = (action or "").upper()

        if action == "INSERT":
            required = [
                "candidate",
                "score",
                "strengths",
                "gaps",
                "recommendation",
                "reason",
            ]
            missing = [field for field in required if field not in kwargs]
            if missing:
                return {
                    "ok": False,
                    "message": f"Missing required fields for INSERT: {', '.join(missing)}",
                }

            record = self.sqlite_service.upsert_candidate(
                name=kwargs["candidate"],
                score=int(kwargs["score"]),
                strengths=kwargs["strengths"],
                gaps=kwargs["gaps"],
                recommendation=kwargs["recommendation"],
                reason=kwargs["reason"],
                web_url=kwargs.get("web_url"),
            )
            return {"ok": True, "message": "Saved successfully.", "record": record}

        if action == "SELECT":
            candidate = kwargs.get("candidate", "")
            record = self.sqlite_service.get_candidate(name=candidate)
            if not record:
                return {"ok": False, "message": f"No record found for {candidate}"}
            return {"ok": True, "record": record}

        if action == "LIST":
            records = self.sqlite_service.list_candidates()
            if not records:
                return {
                    "ok": True,
                    "message": "No candidates in the database yet",
                    "records": [],
                }
            return {"ok": True, "records": records}

        if action == "TOP":
            limit = int(kwargs.get("limit", 3))
            records = self.sqlite_service.top_candidates(limit=limit)
            return {"ok": True, "records": records}

        if action == "DELETE":
            candidate = kwargs.get("candidate", "")
            deleted = self.sqlite_service.delete_candidate(name=candidate)
            if not deleted:
                return {"ok": False, "message": "No record found for that candidate"}
            return {"ok": True, "message": "Candidate deleted successfully."}

        return {"ok": False, "message": f"Unsupported db action: {action}"}
