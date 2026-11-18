"""Дерево синтаксичного виводу SIPL-програми (VIS-01)."""

from pathlib import Path

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput, UnexpectedToken

from .visualization.tree import TreeNode

_GRAMMAR = Path(__file__).with_name("sipl.lark").read_text(encoding="utf-8")
_parser = None

# метазмінні БНФ
META = {"np": "<програма>", "ns": "<оператор>", "na": "<вираз>", "nb": "<умова>"}
TOKEN_META = {"VAR": ("<змінна>", "NV"), "NUMBER": ("<число>", "NN")}

TOKEN_NAMES = {
    "BEGIN": "begin", "END": "end", "IF": "if", "THEN": "then", "ELSE": "else",
    "WHILE": "while", "DO": "do", "SKIP": "skip", "OR": "∨", "OR_W": "or", "NOT": "¬", "NOT_W": "not",
    "ASSIGN": ":=", "SEMI": ";", "PLUS": "+", "MINUS": "–", "TIMES": "*",
    "EQ": "=", "GT": ">", "LPAR": "(", "RPAR": ")", "NUMBER": "число", "VAR": "змінна",
}


class SiplSyntaxError(Exception):
    def __init__(self, message, line, column):
        super().__init__(f"рядок {line}, колонка {column}: {message}")
        self.line = line
        self.column = column


def get_parser():
    global _parser
    if _parser is None:
        _parser = Lark(_GRAMMAR, parser="lalr", lexer="basic", propagate_positions=True)
    return _parser


def _expected(names):
    words = sorted({TOKEN_NAMES.get(n, n) for n in names})
    return ", ".join(f"'{w}'" for w in words)


def parse(text):
    """Повертає дерево розбору Lark або кидає SiplSyntaxError."""
    try:
        return get_parser().parse(text)
    except UnexpectedEOF as e:
        lines = text.splitlines() or [""]
        raise SiplSyntaxError(f"неочікуваний кінець програми, очікувалось {_expected(e.expected)}",
                              len(lines), len(lines[-1]) + 1) from None
    except UnexpectedToken as e:
        if e.token.type == "$END":
            lines = text.splitlines() or [""]
            raise SiplSyntaxError(f"неочікуваний кінець програми, очікувалось {_expected(e.expected)}",
                                  len(lines), len(lines[-1]) + 1) from None
        raise SiplSyntaxError(f"неочікуване '{e.token}', очікувалось {_expected(e.expected)}",
                              e.line, e.column) from None
    except UnexpectedCharacters as e:
        raise SiplSyntaxError(f"недопустимий символ '{text[e.pos_in_stream]}'",
                              e.line, e.column) from None
    except UnexpectedInput as e:
        raise SiplSyntaxError("синтаксична помилка", e.line, e.column) from None


def _token_span(tok, text):
    return {"line": tok.line, "column": tok.column,
            "end_line": tok.end_line, "end_column": tok.end_column,
            "text": text[tok.start_pos:tok.end_pos]}


def _tree_span(t, text):
    m = t.meta
    if m.empty:
        return None
    return {"line": m.line, "column": m.column,
            "end_line": m.end_line, "end_column": m.end_column,
            "text": text[m.start_pos:m.end_pos]}


def _convert(node, text):
    if isinstance(node, Token):
        if node.type in TOKEN_META:
            label, rule = TOKEN_META[node.type]
            sp = _token_span(node, text)
            return TreeNode(label, [TreeNode(str(node), span=sp)], rule=rule, span=sp)
        return TreeNode(str(node), span=_token_span(node, text))
    kind = str(node.data)
    children = [_convert(c, text) for c in node.children]
    return TreeNode(META[kind[:2]], children, rule=kind.upper(), span=_tree_span(node, text))


def build_tree(text):
    """Дерево виводу з метазмінними (<оператор>, <вираз>...) і назвами правил (NS4, NA2...)."""
    t = parse(text)
    if isinstance(t, Tree) and t.data == "start":
        t = t.children[0]
    return _convert(t, text)


def load_tree(path):
    with open(path, encoding="utf-8") as f:
        return build_tree(f.read())
