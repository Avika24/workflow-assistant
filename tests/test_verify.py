from verify import verify_quote, verify_action_items

def test_exact_quote_and_normalized_quote_are_verified():
    original = "Riya will prepare the report by Friday."
    assert verify_quote(original, original)[0] is True
    assert verify_quote("RIYA will prepare\n the report by Friday.", original)[0] is True

def test_fabricated_quote_is_flagged():
    checks = verify_action_items("Aman will finish the database design.",
                                 [{"evidence": "Riya will submit the final report tomorrow."}])
    assert checks[0]["verified"] is False
    assert checks[0]["warning"] == "⚠ not found in source"
