"""
Atalho de execução: `python src/main.py [opções]`.

A implementação vive em `src/laceda_setor/cli.py`; este arquivo só coloca o
diretório `src/` no caminho de importação e delega.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from laceda_setor.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
