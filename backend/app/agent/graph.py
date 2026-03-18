import json
import re
import ast
from typing import Any, Dict, List, Literal, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.agent.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.tools.db_tool import DBTool
from app.tools.jd_scorer import JDScorerTool
from app.tools.web_search import WebSearchTool


class JobMatchState(TypedDict, total=False):
    command: str
    jd: str
    iteration: int
    max_iterations: int
    done: bool

    trace: List[Dict[str, str]]
    last_observation: str

    action: str
    action_input: Dict[str, Any]
    final_answer: str
    final_output: Dict[str, Any]


def _extract_json(payload: str) -> Dict[str, Any]:
    parsed_dicts: List[Dict[str, Any]] = []

    # Prefer fenced JSON if present.
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", payload, flags=re.DOTALL)
    if fenced:
        try:
            candidate = json.loads(fenced.group(1))
            if isinstance(candidate, dict):
                parsed_dicts.append(candidate)
        except json.JSONDecodeError:
            pass

    # Fall back to best-effort object extraction.
    candidates = re.findall(r"\{[\s\S]*?\}", payload, flags=re.DOTALL)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                parsed_dicts.append(parsed)
        except json.JSONDecodeError:
            continue

    # Try parsing python-like dicts (single quotes, True/False).
    for candidate in candidates:
        try:
            parsed = ast.literal_eval(candidate)
            if isinstance(parsed, dict):
                parsed_dicts.append(parsed)
        except (ValueError, SyntaxError):
            continue

    # Last resort: locate the first balanced JSON-like object from braces.
    start = payload.find("{")
    if start != -1:
        depth = 0
        for idx in range(start, len(payload)):
            char = payload[idx]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    block = payload[start : idx + 1]
                    for parser in (json.loads, ast.literal_eval):
                        try:
                            parsed = parser(block)
                            if isinstance(parsed, dict):
                                parsed_dicts.append(parsed)
                        except Exception:
                            pass
                    break

    # Prefer dictionaries that contain the planner action.
    for item in parsed_dicts:
        if "action" in item:
            return item
    for item in parsed_dicts:
        if any(key in item for key in ("thought", "final_answer", "final_output")):
            return item
    return {}


def _format_trace(trace: List[Dict[str, str]]) -> str:
    if not trace:
        return "No steps yet."
    chunks = []
    for idx, item in enumerate(trace, start=1):
        chunks.append(
            f"{idx}. Thought: {item.get('thought', '')}\n"
            f"   Action: {item.get('action', '')}\n"
            f"   Observation: {item.get('observation', '')}"
        )
    return "\n".join(chunks)


def _normalize_action(action: str) -> str:
    cleaned = (action or "").strip().lower().replace("-", "_")
    aliases = {
        "search": "web_search",
        "websearch": "web_search",
        "score": "jd_scorer",
        "score_jd": "jd_scorer",
        "db": "db_tool",
        "database": "db_tool",
        "end": "finish",
        "done": "finish",
    }
    normalized = aliases.get(cleaned, cleaned)
    if normalized not in {"web_search", "jd_scorer", "db_tool", "finish"}:
        return "finish"
    return normalized


def _extract_candidate_name(command: str) -> str:
    # Basic extraction for patterns like "Score Rahul Sharma ..."
    match = re.search(
        r"(?:score|evaluate|assess|screen)\s+([A-Za-z]+(?:\s+[A-Za-z]+){0,2})",
        command,
        flags=re.IGNORECASE,
    )
    if match:
        candidate = match.group(1).strip()
        # Remove trailing prepositions/noise from capture.
        candidate = re.sub(
            r"\b(for|against|to|our|the|this|that|role|position)\b$",
            "",
            candidate,
            flags=re.IGNORECASE,
        ).strip()
        if candidate:
            return candidate

    # Fallback: first multi-word capitalized phrase
    proper_noun = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", command)
    if proper_noun:
        candidate = proper_noun.group(1).strip()
        candidate = re.sub(
            r"\b(for|against|to|our|the|this|that|role|position)\b$",
            "",
            candidate,
            flags=re.IGNORECASE,
        ).strip()
        if candidate:
            return candidate
    return "Candidate"


def _build_final_answer(final_output: Dict[str, Any], last_observation: str = "") -> str:
    if not final_output:
        observation: Dict[str, Any] = {}
        if last_observation:
            try:
                observation = json.loads(last_observation)
            except json.JSONDecodeError:
                observation = {}

        records = observation.get("records")
        if isinstance(records, list):
            if not records:
                return observation.get("message", "No candidates in the database yet.")
            top = records[:3]
            summary = ", ".join(
                f"{item.get('name', 'Unknown')} ({item.get('score', 'N/A')}/100)"
                for item in top
            )
            return f"Found {len(records)} candidate record(s). Top results: {summary}."

        record = observation.get("record")
        if isinstance(record, dict) and record:
            return (
                f"{record.get('name', 'Candidate')} record retrieved. "
                f"Score: {record.get('score', 'N/A')}/100. "
                f"Recommendation: {record.get('recommendation', 'N/A')}."
            )

        message = observation.get("message")
        if message:
            return str(message)

        return "Task completed."

    name = final_output.get("name", "Candidate")
    score = final_output.get("score", "N/A")
    recommendation = final_output.get("recommendation", "Pending")
    reason = final_output.get("reason", "No reason provided.")

    strengths = final_output.get("strengths", []) or []
    gaps = final_output.get("gaps", []) or []
    top_strength = strengths[0] if strengths else "No strengths captured"
    top_gap = gaps[0] if gaps else "No clear gap captured"

    return (
        f"{name} scored {score}/100. Strength: {top_strength}. "
        f"Gap: {top_gap}. Recommend: {recommendation}. Reason: {reason}"
    )


class JobMatchAgent:
    def __init__(
        self,
        *,
        google_api_key: str,
        gemini_model: str,
        gemini_temp: float,
        max_iterations: int,
        web_search_tool: WebSearchTool,
        jd_scorer_tool: JDScorerTool,
        db_tool: DBTool,
    ):
        self.llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=google_api_key,
            temperature=gemini_temp,
        )
        self.max_iterations = max_iterations
        self.web_search_tool = web_search_tool
        self.jd_scorer_tool = jd_scorer_tool
        self.db_tool = db_tool
        self.graph = self._build_graph()

    def _fallback_action(self, state: JobMatchState) -> Dict[str, Any]:
        command = state.get("command", "")
        jd = state.get("jd", "")
        final_output = state.get("final_output", {})
        candidate = final_output.get("name") or _extract_candidate_name(command)
        trace = state.get("trace", [])

        command_l = command.lower()
        is_db_only = any(
            phrase in command_l
            for phrase in ["show all", "top", "record", "remove", "delete", "list"]
        )

        if is_db_only and not trace:
            if "top" in command_l:
                return {"action": "db_tool", "action_input": {"action": "TOP", "limit": 3}}
            if any(word in command_l for word in ["remove", "delete"]):
                return {
                    "action": "db_tool",
                    "action_input": {"action": "DELETE", "candidate": candidate},
                }
            if "record" in command_l or "show me" in command_l:
                return {
                    "action": "db_tool",
                    "action_input": {"action": "SELECT", "candidate": candidate},
                }
            return {"action": "db_tool", "action_input": {"action": "LIST"}}

        # Evaluation flow fallback:
        has_web = any("web_search(" in step.get("action", "") for step in trace)
        has_score = any("jd_scorer(" in step.get("action", "") for step in trace)
        has_insert = any(
            "db_tool(" in step.get("action", "") and '"INSERT"' in step.get("action", "")
            for step in trace
        )
        has_select = any(
            "db_tool(" in step.get("action", "") and '"SELECT"' in step.get("action", "")
            for step in trace
        )

        if not has_web:
            return {
                "action": "web_search",
                "action_input": {
                    "query": f"{candidate} Python developer GitHub LinkedIn portfolio"
                },
            }

        if not has_score:
            profile = state.get("last_observation", "") or "Limited public profile evidence."
            return {
                "action": "jd_scorer",
                "action_input": {
                    "candidate": candidate,
                    "profile": profile,
                    "jd": jd,
                    "command": command,
                },
            }

        if not has_insert:
            return {
                "action": "db_tool",
                "action_input": {
                    "action": "INSERT",
                    "candidate": final_output.get("name", candidate),
                    "score": final_output.get("score", 50),
                    "strengths": final_output.get("strengths", []),
                    "gaps": final_output.get("gaps", []),
                    "recommendation": final_output.get(
                        "recommendation", "Insufficient Info — Request Resume"
                    ),
                    "reason": final_output.get(
                        "reason", "Generated from available profile evidence."
                    ),
                    "web_url": final_output.get("web_url", ""),
                },
            }

        if not has_select:
            return {
                "action": "db_tool",
                "action_input": {"action": "SELECT", "candidate": final_output.get("name", candidate)},
            }

        return {"action": "finish", "action_input": {}}

    def _agent_node(self, state: JobMatchState) -> JobMatchState:
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", self.max_iterations)

        if iteration >= max_iterations:
            return {
                "done": True,
                "final_answer": "Max iteration reached. Returning the best collected result so far.",
            }

        prompt = USER_PROMPT_TEMPLATE.format(
            command=state.get("command", ""),
            jd=state.get("jd", ""),
            iteration=iteration + 1,
            max_iterations=max_iterations,
            trace=_format_trace(state.get("trace", [])),
            last_observation=state.get("last_observation", "None"),
        )

        parsed: Dict[str, Any] = {}
        try:
            response = self.llm.invoke(f"{SYSTEM_PROMPT}\n\n{prompt}")
            parsed = _extract_json(str(response.content))
        except Exception:
            parsed = {}

        if parsed:
            action = _normalize_action(parsed.get("action", "finish"))
            action_input = parsed.get("action_input", {})
            if not isinstance(action_input, dict):
                action_input = {}
            thought = parsed.get("thought", "Proceeding with next step.")
        else:
            fallback = self._fallback_action(state)
            action = fallback["action"]
            action_input = fallback["action_input"]
            thought = "Using deterministic fallback step because model output was malformed."

        # Enforce required flow: after INSERT, force SELECT before finish for evaluation commands.
        command_l = state.get("command", "").lower()
        is_db_only = any(
            phrase in command_l
            for phrase in ["show all", "top", "record", "remove", "delete", "list"]
        )
        previous_trace = state.get("trace", [])
        has_insert = any(
            "db_tool(" in step.get("action", "") and '"INSERT"' in step.get("action", "")
            for step in previous_trace
        )
        has_select = any(
            "db_tool(" in step.get("action", "") and '"SELECT"' in step.get("action", "")
            for step in previous_trace
        )
        if action == "finish" and has_insert and not has_select and not is_db_only:
            action = "db_tool"
            action_input = {
                "action": "SELECT",
                "candidate": state.get("final_output", {}).get("name")
                or _extract_candidate_name(state.get("command", "")),
            }
            thought = "Verifying saved record before final answer."

        trace = list(previous_trace)
        trace.append(
            {
                "thought": thought,
                "action": f"{action}({json.dumps(action_input, ensure_ascii=False)})",
                "observation": "",
            }
        )

        updates: JobMatchState = {
            "iteration": iteration + 1,
            "trace": trace,
            "action": action,
            "action_input": action_input,
            "done": action == "finish",
        }

        if action == "finish":
            updates["final_output"] = state.get("final_output", {})
            updates["final_answer"] = parsed.get(
                "final_answer",
                _build_final_answer(updates["final_output"]),
            )

        return updates

    def _tool_node(self, state: JobMatchState) -> JobMatchState:
        action = state.get("action", "")
        action_input = state.get("action_input", {})
        result: Dict[str, Any]

        try:
            if action == "web_search":
                query = action_input.get("query", "").strip() if isinstance(action_input, dict) else ""
                if not query:
                    query = (
                        f"{_extract_candidate_name(state.get('command', ''))} "
                        "Python developer GitHub LinkedIn portfolio"
                    )
                result = self.web_search_tool.run(query=query)
                if result.get("best_url"):
                    final_output = dict(state.get("final_output", {}))
                    final_output["name"] = final_output.get("name") or _extract_candidate_name(
                        state.get("command", "")
                    )
                    final_output["web_url"] = result["best_url"]
                    final_output["profile_summary"] = result.get("summary", "")
                    state["final_output"] = final_output

            elif action == "jd_scorer":
                final_output = dict(state.get("final_output", {}))
                candidate = (
                    action_input.get("candidate")
                    or final_output.get("name")
                    or _extract_candidate_name(state.get("command", ""))
                )
                profile = (
                    action_input.get("profile")
                    or final_output.get("profile_summary")
                    or state.get("last_observation", "")
                    or "Limited profile evidence."
                )
                jd = action_input.get("jd") or state.get("jd", "")
                command = action_input.get("command") or state.get("command", "")

                result = self.jd_scorer_tool.run(
                    candidate=candidate,
                    profile=profile,
                    jd=jd,
                    command=command,
                )
                merged = final_output
                merged.update(
                    {
                        "name": candidate,
                        "score": result.get("score", 0),
                        "strengths": result.get("strengths", []),
                        "gaps": result.get("gaps", []),
                        "recommendation": result.get("recommendation", ""),
                        "reason": result.get("reason", ""),
                    }
                )
                state["final_output"] = merged

            elif action == "db_tool":
                merged = dict(state.get("final_output", {}))
                payload = dict(action_input)
                db_action = (payload.get("action", "") or "").upper()

                if db_action == "INSERT":
                    payload = {
                        "action": "INSERT",
                        "candidate": payload.get("candidate") or merged.get("name") or _extract_candidate_name(state.get("command", "")),
                        "score": payload.get("score", merged.get("score", 50)),
                        "strengths": payload.get("strengths", merged.get("strengths", [])),
                        "gaps": payload.get("gaps", merged.get("gaps", [])),
                        "recommendation": payload.get(
                            "recommendation",
                            merged.get("recommendation", "Insufficient Info — Request Resume"),
                        ),
                        "reason": payload.get(
                            "reason",
                            merged.get("reason", "Generated from available evidence."),
                        ),
                        "web_url": payload.get("web_url", merged.get("web_url", "")),
                    }
                elif db_action in {"SELECT", "DELETE"}:
                    payload["candidate"] = payload.get("candidate") or merged.get("name") or _extract_candidate_name(
                        state.get("command", "")
                    )
                elif db_action == "TOP":
                    payload["limit"] = int(payload.get("limit", 3))

                result = self.db_tool.run(**payload)

                if db_action == "SELECT" and result.get("record"):
                    state["final_output"] = {
                        "name": result["record"].get("name", ""),
                        "score": result["record"].get("score", 0),
                        "strengths": result["record"].get("strengths", []),
                        "gaps": result["record"].get("gaps", []),
                        "recommendation": result["record"].get("recommendation", ""),
                        "reason": result["record"].get("reason", ""),
                        "web_url": result["record"].get("web_url", ""),
                    }
            else:
                result = {"ok": False, "message": f"Unknown action: {action}"}

        except Exception as exc:
            result = {"ok": False, "message": f"Tool execution failed: {str(exc)}"}

        observation = json.dumps(result, ensure_ascii=False)
        trace = state.get("trace", [])
        if trace:
            trace[-1]["observation"] = observation

        return {
            "trace": trace,
            "last_observation": observation,
            "final_output": state.get("final_output", {}),
        }

    @staticmethod
    def _router(state: JobMatchState) -> Literal["tool", "__end__"]:
        return END if state.get("done") else "tool"

    def _build_graph(self):
        graph = StateGraph(JobMatchState)

        graph.add_node("agent", self._agent_node)
        graph.add_node("tool", self._tool_node)

        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", self._router, {"tool": "tool", END: END})
        graph.add_edge("tool", "agent")

        return graph.compile()

    def run(self, *, command: str, jd: str) -> Dict[str, Any]:
        output = self.graph.invoke(
            {
                "command": command,
                "jd": jd,
                "iteration": 0,
                "max_iterations": self.max_iterations,
                "done": False,
                "trace": [],
                "last_observation": "None",
                "final_output": {},
            }
        )

        final_output = output.get("final_output", {})

        if not output.get("final_answer"):
            output["final_answer"] = _build_final_answer(
                final_output,
                output.get("last_observation", ""),
            )

        trace = output.get("trace", [])
        # Remove repeated terminal finish entries if any.
        cleaned_trace: List[Dict[str, Any]] = []
        for item in trace:
            if (
                cleaned_trace
                and item.get("action", "").startswith("finish(")
                and cleaned_trace[-1].get("action", "").startswith("finish(")
            ):
                continue
            cleaned_trace.append(item)

        return {
            "final_answer": output.get("final_answer", "Completed."),
            "result": final_output,
            "trace": cleaned_trace,
        }
