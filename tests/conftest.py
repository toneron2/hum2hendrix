"""Make the src/ packages importable without installing the project."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Headless plotting for the visualization tests
import matplotlib  # noqa: E402

matplotlib.use('Agg')
