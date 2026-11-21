from dataclasses import replace
from arena.dedup import fingerprint, is_repeat, unique_facts


def test_same_fact_different_url(fact):
    other = replace(fact, url="https://elsewhere.test/story")
    assert len(unique_facts([fact, other], [])) == 1
    assert is_repeat(other.text, [fingerprint(fact.text)])


def test_different_fact(fact):
    assert not is_repeat("On 2026-11-19 the civic transit bill passed with 80 votes.", [fact.text])


def test_date_normalization():
    assert fingerprint("On 22 November 2026 output rose 1,000.") == fingerprint("On Nov. 22, 2026 output rose 1000.")


def test_known_context_and_empty(fact):
    assert not unique_facts([fact], [fact.text])
    assert unique_facts([], []) == []
