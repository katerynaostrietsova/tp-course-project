from sipl.formal.equations import make_predicate
from sipl.formal.grammar import parse_grammar
from sipl.formal.pumping import (check_split, expand_word, explore, grammar_membership,
                                 parse_split, splits)

ABC = make_predicate("w == 'a'*(len(w)//3) + 'b'*(len(w)//3) + 'c'*(len(w)//3)")


def test_splits_conditions():
    for sp in splits("aabbcc", 3):
        assert "".join(sp.parts()) == "aabbcc"
        assert len(sp.t1 + sp.t2) >= 1
        assert len(sp.t1 + sp.x + sp.t2) <= 3


def test_expand_word():
    assert expand_word("a^k b^k c^k", 2) == "aabbcc"
    assert expand_word("a^{k+1} b^{2k}", 2) == "aaabbbb"


def test_abc_not_context_free():
    # лема 4.12: жоден розклад не проходить
    r = explore(expand_word("a^k b^k c^k", 3), 3, ABC)
    assert r["all_refuted"]


def test_anbn_has_good_split():
    m = grammar_membership(parse_grammar("S -> aSb | ε"))
    r = explore("aaabbb", 3, m)
    assert not r["all_refuted"]
    sp = parse_split("aaabbb", "aa|a||b|bb")
    assert not check_split(sp, m).refuted
