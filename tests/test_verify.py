from verify import verify_quote, verify_action_items


def test_verbatim_quote_is_verified():
    ok, score = verify_quote(
        "Riya will prepare the report by Friday.",
        "Riya will prepare the report by Friday.",
    )
    assert ok and score == 1.0


def test_whitespace_and_case_are_normalized():
    ok, _ = verify_quote(
        "RIYA will prepare\n the report by Friday.",
        "Riya will prepare the report by Friday.",
    )
    assert ok


def test_fabricated_quote_is_flagged():
    checks = verify_action_items(
        "Aman will finish the database design.",
        [{"evidence": "Riya will submit the final report tomorrow."}],
    )
    assert checks[0]["verified"] is False
    assert checks[0]["warning"] == "⚠ not found in source"
