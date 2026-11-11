"""One disposable Neo4j instance per arm, started and removed with Docker Compose."""
import asyncio
import os
import subprocess
import time

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import DriverError, Neo4jError

from claim_trace.config import ROOT, Settings
from claim_trace.constants import (
    ARMS,
    BOLT_CONNECT_TIMEOUT_SECONDS,
    BOLT_RETRY_SECONDS,
    BOLT_URI,
    BOLT_WAIT_SECONDS,
    COMPOSE_FILE,
    COMPOSE_PROJECT,
    DOCKER,
    NEO4J_USERNAME,
)
from claim_trace.logger import get_logger

log = get_logger(__name__)


def ports(settings: Settings, arm: str) -> tuple[int, int]:
    index = ARMS.index(arm)
    return settings.base_http_port + index, settings.base_bolt_port + index


def bolt_uri(settings: Settings, arm: str) -> str:
    return BOLT_URI.format(host=settings.neo4j_host, port=ports(settings, arm)[1])


def project_name(settings: Settings, run_id: str, arm: str) -> str:
    return COMPOSE_PROJECT.format(prefix=settings.compose_project_prefix,
                                  run_id=run_id.lower(), arm=arm)


def _compose(settings: Settings, run_id: str, arm: str, *args: str) -> None:
    http_port, bolt_port = ports(settings, arm)
    env = {
        **os.environ,
        "NEO4J_PASSWORD": settings.neo4j_password.get_secret_value(),
        "NEO4J_HOST": settings.neo4j_host,
        "NEO4J_IMAGE": settings.neo4j_image,
        "HTTP_PORT": str(http_port),
        "BOLT_PORT": str(bolt_port),
    }
    subprocess.run(
        [DOCKER, "compose", "--file", str(ROOT / COMPOSE_FILE),
         "--project-name", project_name(settings, run_id, arm), *args],
        env=env, check=True,
    )


def start(settings: Settings, run_id: str, arm: str) -> None:
    log.info("starting database arm=%s uri=%s", arm, bolt_uri(settings, arm))
    _compose(settings, run_id, arm, "up", "--detach", "--wait")


def stop(settings: Settings, run_id: str, arm: str) -> None:
    log.info("removing database and volume arm=%s", arm)
    _compose(settings, run_id, arm, "down", "--volumes", "--remove-orphans")


async def wait_for_bolt(settings: Settings, arm: str) -> None:
    """Block until a host-side Bolt connection succeeds; container health alone is not enough."""
    uri = bolt_uri(settings, arm)
    auth = (NEO4J_USERNAME, settings.neo4j_password.get_secret_value())
    deadline = time.monotonic() + BOLT_WAIT_SECONDS
    while True:
        try:
            async with AsyncGraphDatabase.driver(
                uri, auth=auth, connection_timeout=BOLT_CONNECT_TIMEOUT_SECONDS
            ) as driver:
                await driver.verify_connectivity()
            log.info("bolt ready uri=%s", uri)
            return
        except (DriverError, Neo4jError, OSError) as error:
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Bolt not ready on {uri} within {BOLT_WAIT_SECONDS}s"
                ) from error
            log.debug("bolt not ready uri=%s error=%s", uri, error)
            await asyncio.sleep(BOLT_RETRY_SECONDS)
