import pytest

from sipl.sipl_tree import SiplSyntaxError, build_tree

GCD = """begin
  while ¬(M = N) do
    if M > N then M := M – N else N := N – M
end"""


def test_gcd():
    t = build_tree(GCD)
    assert t.rule == "NP1"
    assert t.children[1].rule == "NS4"


def test_position():
    t = build_tree("begin\n  x := y + 1\nend")
    s = t.children[1].span
    assert (s["line"], s["column"], s["text"]) == (2, 3, "x := y + 1")


def test_priority():
    t = build_tree("begin if x > 1 then x := 1 else skip; y := a - b * 2 end")
    assert t.children[1].rule == "NS2"
    assert t.children[1].children[2].children[2].rule == "NA4"


def test_syntax_error():
    with pytest.raises(SiplSyntaxError) as e:
        build_tree("begin x := end")
    assert (e.value.line, e.value.column) == (1, 12)
