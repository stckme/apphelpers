try:
    from apphelpers.db.piccolo import *  # noqa: F401, F403

    peewee_enabled = False
    print("apphelpers: using Piccolo")

except ImportError:
    from apphelpers.db.peewee import *  # noqa: F401, F403

    peewee_enabled = True
    print("apphelpers: using Peewee")
