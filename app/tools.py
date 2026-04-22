def summarize_tool(content: str) -> str:
    return f"Summary: {content[:150]}..."


def send_email_tool(target: str, body: str) -> str:
    return f"[SIMULATED] Email sent to {target} with body: {body[:100]}"


def delete_record_tool(record_id: str) -> str:
    return f"[SIMULATED] Record {record_id} deleted."
