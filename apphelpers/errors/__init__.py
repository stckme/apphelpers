try:
    from apphelpers.errors.fastapi import *  # noqa: F401, F403

    print("apphelpers: using FastAPI")
except ImportError:
    from apphelpers.errors.hug import *  # noqa: F401, F403

    print("apphelpers: using hug")
