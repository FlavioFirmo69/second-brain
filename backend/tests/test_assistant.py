from app.assistant import normalize


def test_normalize():
    assert normalize("  Saldo   e Movimenti ") == "saldo e movimenti"

