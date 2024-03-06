try:
    from apphelpers.db.piccolo import *  # noqa: F401, F403

    print("apphelpers: using Piccolo")
except ImportError:
    from apphelpers.db.peewee import *  # noqa: F401, F403

    print("apphelpers: using Peewee")
