import threading


current = threading.local()


def set_context(**context):
    """
    """
    for k, v in context.items():
        setattr(current, k, v)
