"""API gateway: the two routes from D1 (Simplified: Flask routes, not a cloud gateway).

POST /ask       {question, rule_set}   -> {answer_id, status, rule_set, answer, citations, rules}
POST /feedback  {answer_id, rating}    -> {ok: true}
GET  /          the client page

The gateway checks input and turns JSON into calls on the QueryService and
FeedbackLog interfaces. It holds no rule or AI logic.
"""

from pathlib import Path

from flask import Blueprint, jsonify, request, send_from_directory

from riail.feedback.interface import FeedbackLog
from riail.gateway.validation import ValidationError, validate_ask, validate_feedback
from riail.query.service import QueryService

CLIENT_DIR = Path(__file__).resolve().parent.parent / "client"


def create_gateway(query: QueryService, feedback: FeedbackLog, max_question_length: int) -> Blueprint:
    bp = Blueprint("gateway", __name__)

    @bp.get("/")
    def index():
        return send_from_directory(CLIENT_DIR, "index.html")

    @bp.post("/ask")
    def ask():
        try:
            question, rule_set = validate_ask(request.get_json(silent=True), max_question_length)
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        answer = query.ask(question, rule_set)
        return jsonify(answer.to_dict())

    @bp.post("/feedback")
    def give_feedback():
        try:
            answer_id, rating = validate_feedback(request.get_json(silent=True))
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        feedback.record_rating(answer_id, rating)
        return jsonify({"ok": True})

    return bp
