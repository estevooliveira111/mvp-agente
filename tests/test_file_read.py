import json

import tools.file_read as file_read


def _use_base_dir(monkeypatch, tmp_path):
    base_dir = tmp_path / "files"
    base_dir.mkdir()
    monkeypatch.setattr(file_read.settings, "FILE_READ_BASE_DIR", str(base_dir))
    return base_dir


def test_reads_file_inside_base_dir(monkeypatch, tmp_path):
    base_dir = _use_base_dir(monkeypatch, tmp_path)
    (base_dir / "notas.txt").write_text("conteúdo liberado", encoding="utf-8")

    result = json.loads(file_read.execute(file_path="notas.txt"))

    assert result == {"status": "success", "data": "conteúdo liberado"}


def test_blocks_path_traversal(monkeypatch, tmp_path):
    _use_base_dir(monkeypatch, tmp_path)
    (tmp_path / ".env").write_text("JWT_SECRET_KEY=segredo", encoding="utf-8")

    result = json.loads(file_read.execute(file_path="../.env"))

    assert result["status"] == "error"
    assert "segredo" not in json.dumps(result)


def test_blocks_absolute_path(monkeypatch, tmp_path):
    _use_base_dir(monkeypatch, tmp_path)
    secret = tmp_path / "secret.txt"
    secret.write_text("segredo", encoding="utf-8")

    result = json.loads(file_read.execute(file_path=str(secret)))

    assert result["status"] == "error"


def test_blocks_symlink_escaping_base_dir(monkeypatch, tmp_path):
    base_dir = _use_base_dir(monkeypatch, tmp_path)
    secret = tmp_path / "secret.txt"
    secret.write_text("segredo", encoding="utf-8")
    (base_dir / "atalho.txt").symlink_to(secret)

    result = json.loads(file_read.execute(file_path="atalho.txt"))

    assert result["status"] == "error"
