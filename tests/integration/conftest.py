from __future__ import annotations


def pytest_collection_modifyitems(items: list) -> None:
    # Medium tests run last: they may trigger the Freedium fallback (403/429),
    # which adds latency. Keep them at the end so faster providers run first.
    medium = [i for i in items if "test_medium_integration" in i.nodeid]
    others = [i for i in items if "test_medium_integration" not in i.nodeid]
    items[:] = others + medium
