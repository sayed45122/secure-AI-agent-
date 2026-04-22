from fastapi import FastAPI
import logging
import os

from app.models import UserRequest
from app.sandbox import sandbox_parse
from app.agent import build_action_plan
from app.security import verify_intent
from app.security_llm import review_plan_with_llm
from app.tools import summarize_tool, send_email_tool, delete_record_tool

app = FastAPI(title="Secure Autonomous Agent Demo")

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/audit.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


@app.get("/")
def root():
    return {
        "message": "Secure Autonomous Agent Demo is running.",
        "docs": "/docs"
    }


@app.post("/process")
def process_request(req: UserRequest):
    sandboxed = sandbox_parse(req.content)
    plan = build_action_plan(req.user_goal, sandboxed)

    security_source = "llm_reviewer"
    try:
        decision = review_plan_with_llm(req.user_goal, sandboxed, plan)
    except Exception as e:
        security_source = "rule_based_fallback"
        logging.warning(f"LLM security reviewer failed, falling back to rules. Error: {str(e)}")
        decision = verify_intent(req.user_goal, sandboxed, plan)

    logging.info(
        f"user_goal={req.user_goal} | "
        f"suspicious={sandboxed.suspicious_patterns} | "
        f"plan={plan.proposed_action} | "
        f"tool={plan.required_tool} | "
        f"allowed={decision.allowed} | "
        f"risk={decision.risk_score} | "
        f"security_source={security_source}"
    )

    if not decision.allowed:
        return {
            "status": "blocked",
            "security_source": security_source,
            "sandboxed_facts": sandboxed.model_dump(),
            "plan": plan.model_dump(),
            "security_decision": decision.model_dump(),
            "result": None
        }

    if plan.proposed_action == "summarize_content":
        result = summarize_tool(req.content)
    elif plan.proposed_action == "send_email":
        result = send_email_tool("admin@example.com", req.content)
    elif plan.proposed_action == "delete_record":
        result = delete_record_tool("123")
    else:
        result = "No action executed."

    return {
        "status": "approved",
        "security_source": security_source,
        "sandboxed_facts": sandboxed.model_dump(),
        "plan": plan.model_dump(),
        "security_decision": decision.model_dump(),
        "result": result
    }
