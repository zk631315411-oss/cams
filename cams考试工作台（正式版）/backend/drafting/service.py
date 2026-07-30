from __future__ import annotations

from typing import Any

from retrieval.service import retrieve_question_evidence
from storage import WorkspaceStore


def prepare_draft_input(store: WorkspaceStore, question_id: str,
                        config: dict[str, Any] | None = None) -> dict[str, Any]:
    """DS 的标准输入必须由当前题目的完整检索链路生成。"""
    question = store.assert_ds_ready(question_id)
    content = dict(question.get("content") or {})
    for key in ("answer", "reference_answer", "source_answer", "source_reference_answer"):
        content.pop(key, None)
    safe_question = {
        "question_id": question["question_id"],
        "version": question["version"],
        "content": content,
    }
    reviewed = store.read_record(question_id, "evidence_review")
    if reviewed:
        adopted = [item for item in reviewed.get("items", []) if item.get("status") == "adopted"]
        if not adopted:
            raise ValueError("至少采用一条教材依据后才能准备 DS 输入")
        packet = dict(reviewed.get("retrieval") or {})
        packet["retrieval_kind"] = "question_reviewed"
        packet["selected_evidence"] = adopted
        packet["evidence_review_version"] = reviewed.get("version")
    else:
        packet = retrieve_question_evidence(store.root, content, config=config)
    return {"question": safe_question, "evidence_packet": packet}
