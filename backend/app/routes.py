from flask import Blueprint, current_app, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _is_db_only_command(command: str) -> bool:
    lowered = (command or "").lower()
    db_markers = [
        "show all",
        "list",
        "top",
        "show me",
        "record",
        "remove",
        "delete",
    ]
    return any(marker in lowered for marker in db_markers)


@api_bp.get("/health")
def health_check():
    return jsonify({"ok": True, "service": "jobmatch-ai-backend"}), 200


@api_bp.post("/evaluate")
def evaluate_candidate():
    payload = request.get_json(silent=True) or {}
    command = (payload.get("command") or "").strip()
    jd = (payload.get("jd") or "").strip()

    if not command:
        return jsonify({"error": "command is required"}), 400
    if not jd and not _is_db_only_command(command):
        return (
            jsonify(
                {
                    "error": (
                        "jd is required for candidate evaluation commands. "
                        "DB-only commands like list/top/select/delete do not need jd."
                    )
                }
            ),
            400,
        )

    agent = current_app.config["JOBMATCH_AGENT"]

    try:
        result = agent.run(command=command, jd=jd)
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@api_bp.get("/candidates")
def list_candidates():
    db_tool = current_app.config["DB_TOOL"]
    result = db_tool.run(action="LIST")
    return (
        jsonify(
            {
                "candidates": result.get("records", []),
                "message": result.get("message", ""),
            }
        ),
        200,
    )


@api_bp.get("/candidates/top")
def top_candidates():
    try:
        limit = int(request.args.get("limit", 3))
    except (TypeError, ValueError):
        limit = 3
    limit = max(1, min(limit, 50))
    db_tool = current_app.config["DB_TOOL"]
    result = db_tool.run(action="TOP", limit=limit)
    return jsonify({"candidates": result.get("records", [])}), 200


@api_bp.get("/candidates/<string:name>")
def get_candidate(name: str):
    db_tool = current_app.config["DB_TOOL"]
    result = db_tool.run(action="SELECT", candidate=name)
    if not result.get("ok"):
        return jsonify({"error": result.get("message", "No record found")}), 404
    return jsonify({"candidate": result.get("record", {})}), 200


@api_bp.delete("/candidates/<string:name>")
def delete_candidate(name: str):
    db_tool = current_app.config["DB_TOOL"]
    result = db_tool.run(action="DELETE", candidate=name)
    if not result.get("ok"):
        return jsonify({"error": result.get("message", "Delete failed")}), 404
    return jsonify({"message": result.get("message", "Candidate removed")}), 200
