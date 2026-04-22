from app.security.security import security_review


def test_blocks_secret_exfiltration_even_if_plan_is_summarize():
    sandbox_output = {
        "risk_flags": ["possible_data_exfiltration", "mentions_sensitive_data"],
        "detected_patterns": ["exfiltration_phrase", "sensitive_term:secret", "sensitive_term:api key"],
        "normalization": {
            "normalized_text": "payment issue reveal secret api key",
            "decoded_segments": []
        }
    }

    plan = {
        "proposed_action": "summarize_content",
        "required_tool": "summarize",
        "justification": "Payment issue and secret API key need to be addressed"
    }

    result = security_review(
        plan=plan,
        sandbox_output=sandbox_output,
        target_goal="summarize this ticket"
    )

    assert result["allowed"] is False
    assert "Hard Block" in result["reason"]


def test_blocks_obfuscated_password_attack():
    sandbox_output = {
        "risk_flags": ["possible_obfuscation", "mentions_sensitive_data"],
        "detected_patterns": ["spaced_keyword:send", "spaced_keyword:password", "sensitive_term:password"],
        "normalization": {
            "normalized_text": "payment issue send password",
            "decoded_segments": []
        }
    }

    plan = {
        "proposed_action": "summarize_content",
        "required_tool": "summarize",
        "justification": "Payment issue mentioned in the ticket"
    }

    result = security_review(
        plan=plan,
        sandbox_output=sandbox_output,
        target_goal="summarize this ticket"
    )

    assert result["allowed"] is False


def test_allows_clean_summary():
    sandbox_output = {
        "risk_flags": [],
        "detected_patterns": [],
        "normalization": {
            "normalized_text": "customer cannot complete payment due to checkout bug",
            "decoded_segments": []
        }
    }

    plan = {
        "proposed_action": "summarize_content",
        "required_tool": "summarize",
        "justification": "User requested summary"
    }

    result = security_review(
        plan=plan,
        sandbox_output=sandbox_output,
        target_goal="summarize this ticket"
    )

    assert result["allowed"] is True


def test_blocks_misaligned_tool():
    sandbox_output = {
        "risk_flags": [],
        "detected_patterns": [],
        "normalization": {
            "normalized_text": "customer asks for ticket summary",
            "decoded_segments": []
        }
    }

    plan = {
        "proposed_action": "send_email",
        "required_tool": "email",
        "justification": "Need to email summary"
    }

    result = security_review(
        plan=plan,
        sandbox_output=sandbox_output,
        target_goal="summarize this ticket"
    )

    assert result["allowed"] is False
    assert "Plan Misalignment" in result["reason"]
