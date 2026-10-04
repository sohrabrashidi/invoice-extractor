import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


@pytest.fixture(scope="session")
def samples() -> Path:
    # The sample PDFs are generated, not committed. Build them on first use.
    if len(list(SAMPLES.glob("*.pdf"))) < 5:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_samples.py")], check=True)
    return SAMPLES
