from sipl.formal.derivations import analyze, find_derivations
from sipl.formal.grammar import parse_grammar, parse_word


def test_leftmost():
    g = parse_grammar("S -> aSb | ε")
    d = find_derivations(g, parse_word("aabb"))
    assert d[0].short() == "S ⇒ aSb ⇒ aaSbb ⇒ aabb"


def test_rightmost():
    g = parse_grammar("S -> AB\nA -> a\nB -> b")
    d = find_derivations(g, parse_word("ab"), mode="right")
    assert d[0].short() == "S ⇒ AB ⇒ Ab ⇒ ab"


def test_word_not_in_language():
    g = parse_grammar("S -> aSb | ε")
    assert find_derivations(g, parse_word("aab")) == []


def test_ambiguous():
    g = parse_grammar("E -> E - E | a")
    r = analyze(g, parse_word("a-a-a"))
    assert r["ambiguous"]
    assert len(r["trees"]) == 2
