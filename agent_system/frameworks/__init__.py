"""One module per framework. Each exposes ``run(request: str) -> str``.

Framework packages are imported inside ``run`` so the core, tests and the
offline pipeline work without them installed.
"""
