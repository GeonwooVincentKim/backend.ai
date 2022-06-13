from __future__ import annotations
from typing import Tuple

from unittest import mock

import pytest
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis.asyncio.sentinel import Sentinel

from ai.backend.common.redis import execute
from ai.backend.common.types import HostPortPair, RedisConnectionInfo

from .types import RedisClusterInfo


@pytest.mark.redis
@pytest.mark.asyncio
async def test_pipeline_single_instance(redis_container: Tuple[str, HostPortPair]) -> None:
    addr = redis_container[1]
    rconn = RedisConnectionInfo(
        Redis.from_url(url=f'redis://{addr.host}:{addr.port}', socket_timeout=0.5),
        service_name=None,
    )

    def _build_pipeline(r: Redis) -> Pipeline:
        pipe = r.pipeline(transaction=False)
        pipe.set("xyz", "123")
        pipe.incr("xyz")
        return pipe

    results = await execute(rconn, _build_pipeline)
    assert results[0] is True
    assert str(results[1]) == "124"

    actual_value = await execute(rconn, lambda r: r.get("xyz"))
    assert actual_value == b"124"

    async def _build_pipeline_async(r: Redis) -> Pipeline:
        pipe = r.pipeline(transaction=False)
        pipe.set("abc", "123")
        pipe.incr("abc")
        return pipe

    results = await execute(rconn, _build_pipeline_async)
    assert results[0] is True
    assert str(results[1]) == "124"

    actual_value = await execute(rconn, lambda r: r.get("abc"))
    assert actual_value == b"124"


@pytest.mark.redis
@pytest.mark.asyncio
async def test_pipeline_single_instance_retries(redis_container: Tuple[str, HostPortPair]) -> None:
    addr = redis_container[1]
    rconn = RedisConnectionInfo(
        Redis.from_url(url=f'redis://{addr.host}:{addr.port}', socket_timeout=0.5),
        service_name=None,
    )

    build_count = 0

    patcher = mock.patch(
        'redis.asyncio.client.Pipeline._execute_pipeline',
        side_effect=[ConnectionResetError, ConnectionResetError, mock.DEFAULT],
    )
    patcher.start()

    def _build_pipeline(r: Redis) -> Pipeline:
        nonlocal build_count, patcher
        build_count += 1
        if build_count == 3:
            # Restore the original function.
            patcher.stop()
        pipe = r.pipeline(transaction=False)
        pipe.set("xyz", "123")
        pipe.incr("xyz")
        return pipe

    results = await execute(rconn, _build_pipeline, reconnect_poll_interval=0.01)
    assert build_count == 3
    assert results[0] is True
    assert results[1] == 124

    actual_value = await execute(rconn, lambda r: r.get("xyz"))
    assert actual_value == b"124"

    build_count = 0

    patcher = mock.patch(
        'redis.asyncio.client.Pipeline._execute_pipeline',
        side_effect=[ConnectionResetError, ConnectionResetError, mock.DEFAULT],
    )
    patcher.start()

    async def _build_pipeline_async(r: Redis) -> Pipeline:
        nonlocal build_count, patcher
        build_count += 1
        if build_count == 3:
            # Restore the original function.
            patcher.stop()
        pipe = r.pipeline(transaction=False)
        pipe.set("abc", "456")
        pipe.incr("abc")
        return pipe

    results = await execute(rconn, _build_pipeline_async, reconnect_poll_interval=0.01)
    assert build_count == 3
    assert results[0] is True
    assert results[1] == 457

    actual_value = await execute(rconn, lambda r: r.get("abc"))
    assert actual_value == b"457"


@pytest.mark.redis
@pytest.mark.asyncio
async def test_pipeline_sentinel_cluster(redis_cluster: RedisClusterInfo) -> None:
    rconn = RedisConnectionInfo(
        Sentinel(
            redis_cluster.sentinel_addrs,
            password='develove',
            socket_timeout=0.5,
        ),
        service_name='mymaster',
    )

    def _build_pipeline(r: Redis) -> Pipeline:
        pipe = r.pipeline(transaction=False)
        pipe.set("xyz", "123")
        pipe.incr("xyz")
        return pipe

    results = await execute(rconn, _build_pipeline)
    assert results[0] is True
    assert str(results[1]) == "124"
