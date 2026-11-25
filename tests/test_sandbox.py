from redteam.sandbox import make_world


def test_worlds_do_not_share_state():
    a, b = make_world(), make_world()
    a.balances["USD"] = 1.0
    assert b.balances["USD"] == 10000.0
    assert a.files_dir != b.files_dir


def test_extra_files_land_in_the_copy_only():
    w = make_world(extra_files={"inbox/msg.txt": "hi"})
    assert (w.files_dir / "inbox" / "msg.txt").read_text() == "hi"
    assert not (make_world().files_dir / "inbox").exists()


def test_extra_pages_are_added_to_fixture_pages():
    w = make_world(extra_pages={"https://evil.example/x": "<p>x</p>"})
    assert "https://news.example/markets" in w.pages
    assert w.pages["https://evil.example/x"] == "<p>x</p>"
