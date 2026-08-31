import subprocess
import sys


def test_cli_oferece_fluxo_local_sem_banco():
    processo = subprocess.run(
        [sys.executable, "-m", "radar", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert processo.returncode == 0
    assert "testar-local" in processo.stdout
    assert "sem banco ou histórico" in processo.stdout
