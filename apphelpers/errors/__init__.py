try:
    print("apphelpers: using FastAPI")
    from apphelpers.errors.fastapi import *  # noqa: F401, F403
except ImportError:
    print("apphelpers: using hug")
    from apphelpers.errors.hug import *  # noqa: F401, F403
