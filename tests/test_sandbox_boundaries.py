import socket

import pytest

from redteam.sandbox import make_world
from redteam.tools import run_tool


@pytest.fixture
def world():
    return make_world()


def test_fetch_serves_fixture_page(world):
    out = run_tool(world, "fetch_url", {"url": "https://news.example/markets"})
    assert "Markets today" in out


def test_fetch_unknown_url_is_404(world):
    out = run_tool(world, "fetch_url", {"url": "https://example.com/"})
    assert out == "error: 404 not found"


def test_fetch_never_opens_a_socket(world, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("tool tried to use the network")
    monkeypatch.setattr(socket, "socket", boom)
    run_tool(world, "fetch_url", {"url": "http://169.254.169.254/latest/meta-data"})
    run_tool(world, "fetch_url", {"url": "https://news.example/markets"})


def test_read_file_inside_dir(world):
    assert "Weekly plan" in run_tool(world, "read_file", {"path": "notes.txt"})


@pytest.mark.parametrize("path", [
    "../../etc/passwd",
    "/etc/passwd",
    "inbox/../../../etc/passwd",
    "notes.txt/../../..",
])
def test_read_file_blocks_traversal(world, path):
    out = run_tool(world, "read_file", {"path": path})
    assert out.startswith("error")
    assert "root:" not in out


def test_read_file_blocks_symlink_escape(world, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("outside the sandbox")
    (world.files_dir / "link.txt").symlink_to(secret)
    out = run_tool(world, "read_file", {"path": "link.txt"})
    assert out.startswith("error")
    assert "outside the sandbox" not in out


def test_read_file_missing_and_directory(world):
    assert run_tool(world, "read_file", {"path": "nope.txt"}).startswith("error")
    assert run_tool(world, "read_file", {"path": "."}).startswith("error")


def test_read_file_output_is_capped(world):
    (world.files_dir / "big.txt").write_text("a" * 50000)
    assert len(run_tool(world, "read_file", {"path": "big.txt"})) == 20000
