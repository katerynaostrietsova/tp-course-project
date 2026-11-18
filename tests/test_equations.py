from sipl.formal.equations import (approximations, compare_with_grammar, compare_with_language,
                                   from_grammar, interpret, is_solution, make_predicate,
                                   parse_expr, parse_system, to_grammar)
from sipl.formal.grammar import parse_grammar


def test_interpretation_example_4_29():
    nu = {"X": {"a", "ab"}, "Y": {"", "b", "cc"}, "Z": {"bb", "c"}}
    r = interpret(parse_expr("X X Z {a} Y"), nu)
    assert len(r) == 24
    assert {"aabba", "ababcab", "aacacc"} <= r


def test_approximations_example_4_30():
    s = parse_system("S = {ε} ∪ {a}S{b}")
    r = [x["S"] for x in approximations(s, 6)]
    assert r[:4] == [set(), {""}, {"", "ab"}, {"", "ab", "aabb"}]


def test_ss_has_many_solutions():
    s = parse_system("S = S S")
    assert approximations(s, 4)[-1]["S"] == set()
    assert is_solution(s, {"S": {""}}, 4)


def test_same_as_grammar():
    g = parse_grammar("E -> E + T | T\nT -> T * F | F\nF -> (E) | a")
    assert compare_with_grammar(from_grammar(g), 5)["equal"]


def test_constructor():
    g = to_grammar(parse_system("S = {a}S{b} ∪ {ε}"))
    r = compare_with_language(g, make_predicate("w.count('a') == w.count('b')"), 4)
    assert not r["ok"]
    assert "ba" in r["missing"] and r["extra"] == set()
