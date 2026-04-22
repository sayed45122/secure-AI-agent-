from app.models import SandboxedFacts, ActionPlan
from app.llm_client import call_llm_for_plan


def build_action_plan(user_goal: str, sandboxed: SandboxedFacts) -> ActionPlan:
    llm_result = call_llm_for_plan(
        user_goal=user_goal,
        sandbox_summary=sandboxed.raw_summary,
        extracted_facts=sandboxed.extracted_facts
    )

    return ActionPlan(
        proposed_action=llm_result.get("proposed_action", "summarize_content"),
        target_resource=llm_result.get("target_resource", "ticket"),
        justification=llm_result.get("justification", "No justification provided."),
        required_tool=llm_result.get("required_tool", "none")
    )
