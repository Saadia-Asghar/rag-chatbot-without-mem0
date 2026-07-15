"""Cheap checks run before local RAG retrieval or answer generation."""

import re


def block_reason(text: str) -> str | None:
    lower = text.lower()
    if any(phrase in lower for phrase in ("ignore previous instructions", "reveal system prompt", "show your prompt")):
        return "I can help with your support issue, but I cannot follow instructions that override the support workflow."
    if any(word in lower for word in ("password", "one-time code", "otp", "cvv")) or re.search(r"\b(?:\d[ -]?){13,16}\b", text):
        return "For your security, do not send passwords, one-time codes, CVV values, or full card numbers. Please share an invoice reference or the exact error instead."
    return None
