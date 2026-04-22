import json
from dotenv import load_dotenv

load_dotenv()

from app.sandbox import sandbox_parse
from app.agent import build_action_plan
from app.security import verify_intent

try:
    from app.security import verify_intent
    HAS_LLM_REVIEWER = True
except Exception:
    HAS_LLM_REVIEWER = False


USE_LLM_REVIEWER = False


def evaluate(path="data/tickets.json"):
    with open(path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total_samples = len(samples)
    total_benign = 0
    total_malicious = 0
    blocked_benign = 0
    blocked_malicious = 0
    correct_predictions = 0

    print("\n" + "=" * 60)
    print("🚀 Starting Secure Agent Evaluation")
    print("=" * 60 + "\n")

    for i, sample in enumerate(samples, start=1):
        sandboxed = sandbox_parse(sample["content"])
        plan = build_action_plan(sample["user_goal"], sandboxed)

        if USE_LLM_REVIEWER and HAS_LLM_REVIEWER:
            try:
                decision = review_plan_with_llm(sample["user_goal"], sandboxed, plan)
                security_source = "llm_reviewer"
            except Exception:
                decision = verify_intent(sample["user_goal"], sandboxed, plan)
                security_source = "rule_based_fallback"
        else:
            decision = verify_intent(sample["user_goal"], sandboxed, plan)
            security_source = "rule_based"

        label = sample["label"]

        if label == "benign":
            total_benign += 1
            if decision.allowed:
                correct_predictions += 1
            else:
                blocked_benign += 1

        elif label == "malicious":
            total_malicious += 1
            if not decision.allowed:
                correct_predictions += 1
                blocked_malicious += 1

        print(f"Sample #{i}")
        print(f"Label: {label}")
        print(f"Security Source: {security_source}")
        print(f"Allowed: {decision.allowed}")
        print(f"Risk Score: {decision.risk_score}")
        print(f"Reason: {decision.reason}")
        print("-" * 60)

    asr = (
        (total_malicious - blocked_malicious) / total_malicious
        if total_malicious else 0.0
    )

    fpr = (
        blocked_benign / total_benign
        if total_benign else 0.0
    )

    fsr = (
        correct_predictions / total_samples
        if total_samples else 0.0
    )

    print("\n" + "=" * 60)
    print("✅ Final Metrics")
    print("=" * 60)
    print(f"Total samples: {total_samples}")
    print(f"Total benign: {total_benign}")
    print(f"Total malicious: {total_malicious}")
    print(f"Blocked malicious: {blocked_malicious}")
    print(f"Blocked benign: {blocked_benign}")
    print(f"Correct predictions: {correct_predictions}")
    print(f"ASR (Attack Success Rate): {asr * 100:.2f}%")
    print(f"FPR (False Positive Rate): {fpr * 100:.2f}%")
    print(f"FSR (Full Security Rate): {fsr * 100:.2f}%")


if __name__ == "__main__":
    evaluate()