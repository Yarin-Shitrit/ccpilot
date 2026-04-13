from ccpilot.swarm import mailbox


def test_task_lifecycle(tmp_path):
    mb = mailbox.Mailbox(tmp_path / "mb.sqlite")
    tid = mb.post_task("explorer", {"q": "audit"})
    task = mb.claim("explorer")
    assert task and task.id == tid and task.payload["q"] == "audit"
    assert mb.claim("explorer") is None  # nothing left
    mb.finish(tid, {"ok": True, "found": 3})
    assert mb.results([tid])[tid]["found"] == 3


def test_messages(tmp_path):
    mb = mailbox.Mailbox(tmp_path / "mb.sqlite")
    mb.send("coord", "worker-1", {"hint": "check src/"})
    inbox = mb.inbox("worker-1")
    assert len(inbox) == 1 and inbox[0]["body"]["hint"] == "check src/"
    assert mb.inbox("worker-1") == []  # marked read
