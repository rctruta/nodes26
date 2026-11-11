import subprocess

from claim_trace import databases


def test_each_arm_gets_its_own_ports_and_project(settings):
    assert databases.ports(settings, "control") == (7000, 8000)
    assert databases.ports(settings, "distinct") == (7003, 8003)
    assert databases.bolt_uri(settings, "copies") == "bolt://localhost:8002"
    assert databases.project_name(settings, "20260101T000000Z", "single") == (
        "trace-20260101t000000z-single")


def test_start_and_stop_drive_compose_with_the_arm_environment(settings, monkeypatch):
    seen = []

    def fake_run(command, env, check):
        seen.append((command, env, check))

    monkeypatch.setattr(subprocess, "run", fake_run)
    databases.start(settings, "20260101T000000Z", "single")
    databases.stop(settings, "20260101T000000Z", "single")
    (up, env, check), (down, _, _) = seen
    assert up[:2] == ["docker", "compose"] and up[-3:] == ["up", "--detach", "--wait"]
    assert "trace-20260101t000000z-single" in up
    assert down[-3:] == ["down", "--volumes", "--remove-orphans"]
    assert check is True
    assert (env["HTTP_PORT"], env["BOLT_PORT"]) == ("7001", "8001")
    assert env["NEO4J_PASSWORD"] == "test-password"
    assert env["NEO4J_IMAGE"] == "neo4j:test"
