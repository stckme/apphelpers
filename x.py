from functools import wraps


def honeybadger_wrapper(hb):
    """
    wrapper that executes the function in a try/except
    If an exception occurs, it is first reported to Honeybadger
    """
    def wrapper(f):
        @wraps(f)
        def f_wrapped(*args, **kw):
            try:
                ret = f(*args, **kw)
            except Exception as e:
                hb.notify(
                    e,
                    context={
                        'func': f.__name__,
                        'kwargs': filter_dict(kw, settings.HB_PARAM_FILTERS)
                    }
                )
                raise e
            return ret
        return f_wrapped
    return wrapper

