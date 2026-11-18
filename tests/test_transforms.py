from sipl.formal.grammar import language_up_to, parse_grammar
from sipl.formal.transforms import is_cnf, reduce_grammar, remove_eps, to_cnf


def test_reduce_example_4_19():
    g = parse_grammar("S -> a | A\nA -> AB\nB -> b\nC -> c")
    r = reduce_grammar(g)
    assert r.rules == [("S", ("a",))]
    assert r.terminals == {"a"}


def test_remove_eps_example_4_20():
    g = parse_grammar("S -> aSb | bSa | ε")
    r = remove_eps(g)
    assert set(r.rules) == {("S", tuple("aSb")), ("S", tuple("bSa")),
                            ("S", tuple("ab")), ("S", tuple("ba"))}


def test_cnf_example_4_21():
    g = parse_grammar("S -> ε | abSc")
    r = to_cnf(g)
    assert is_cnf(r)
    assert language_up_to(r, 9) == language_up_to(g, 9)


def test_cnf_other_grammars():
    for text in ["E -> E + T | T\nT -> T * F | F\nF -> (E) | a",
                 "S -> SS | (S) | ε",
                 "S -> A\nA -> B\nB -> ab"]:
        g = parse_grammar(text)
        r = to_cnf(g)
        assert is_cnf(r)
        assert language_up_to(r, 6) == language_up_to(g, 6)


def test_not_cnf():
    assert not is_cnf(parse_grammar("S -> aSb | ε"))
