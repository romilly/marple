"""Install the MARPLE Jupyter kernelspec."""

import json
import shutil
import tempfile
from pathlib import Path

from jupyter_client.kernelspec import KernelSpecManager

KERNEL_JSON = {
    "argv": ["python", "-m", "marple.jupyter", "-f", "{connection_file}"],
    "display_name": "MARPLE (APL)",
    "language": "apl",
    "interrupt_mode": "signal",
}


def install_kernel(user: bool = True) -> None:
    """Install the MARPLE kernelspec."""
    resources = Path(__file__).parent / "resources"
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / "kernel.json").write_text(json.dumps(KERNEL_JSON, indent=2))
        for fname in ["logo-32x32.png", "logo-64x64.png", "kernel.js"]:
            src = resources / fname
            if src.exists():
                shutil.copy(src, td_path)
        KernelSpecManager().install_kernel_spec(
            str(td_path), "marple", user=user)
    print("MARPLE kernel installed. Run: jupyter notebook")


if __name__ == "__main__":
    install_kernel()
