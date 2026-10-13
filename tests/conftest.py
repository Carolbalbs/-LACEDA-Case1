"""Coloca `src/` no caminho de importação para os testes acharem `laceda_setor`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
