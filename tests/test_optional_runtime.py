import subprocess
import sys


def test_base_package_import_does_not_require_torch():
    script = """
import builtins

real_import = builtins.__import__

def block_torch(name, *args, **kwargs):
    if name == "torch" or name.startswith("torch."):
        raise ModuleNotFoundError("torch intentionally blocked for lazy-import test")
    return real_import(name, *args, **kwargs)

builtins.__import__ = block_torch
import isoprax
from isoprax import EBJEPAConfig, EBJEPAWorldModel

assert "torch" not in __import__("sys").modules
try:
    EBJEPAWorldModel(EBJEPAConfig())
except RuntimeError as error:
    assert "optional PyTorch" in str(error)
else:
    raise AssertionError("the optional backend should fail clearly when torch is absent")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
