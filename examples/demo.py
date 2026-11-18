# Запуск прикладів без командного рядка (у PyCharm: правий клік -> Run 'demo')
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sipl.cli import main  # noqa: E402

G = ROOT / "examples" / "grammars"
P = ROOT / "examples" / "sipl"

print("=== FORM-01: зведена граматика, приклад 4.19 ===")
main(["cfg", "reduce", str(G / "ex4_19.txt"), "--explain"])

print("\n=== FORM-01: НФХ, приклад 4.21 ===")
main(["cfg", "cnf", str(G / "ex4_21.txt"), "--explain"])

print("\n=== FORM-04: виводи слова a-a-a ===")
main(["derive", str(G / "minus.txt"), "a-a-a"])

print("\n=== FORM-02: рівняння S = {ε} ∪ {a}S{b} ===")
main(["eq", "solve", str(ROOT / "examples" / "equations" / "ex4_30.txt")])

print("\n=== FORM-03: лема про накачку для a^k b^k c^k ===")
main(["pump", "--lang", "w == 'a'*(len(w)//3) + 'b'*(len(w)//3) + 'c'*(len(w)//3)",
      "--k", "2", "--word", "a^k b^k c^k"])

print("\n=== VIS-01: дерево виводу програми GCD ===")
main(["tree", str(P / "gcd.sipl")])
