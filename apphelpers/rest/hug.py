from apphelpers.db.peewee import dbtransaction


def phony(f):
    return f


class APIFactory:

    def __init__(self, router):
        self.router = router
        self.db_tr_wrapper = phony

    def setup_db_transaction(self, db):
        self.db_tr_wrapper = dbtransaction(db)

    def build(self, f):
        return self.db_tr_wrapper(f)

    def get(self, *a, **k):
        def _wrapper(f):
            return self.router.get(*a, **k)(self.build(f))
        return _wrapper

    def post(self, *a, **k):
        def _wrapper(f):
            return self.router.post(*a, **k)(self.build(f))
        return _wrapper

    def patch(self, *a, **k):
        def _wrapper(f):
            return self.router.patch(*a, **k)(self.build(f))
        return _wrapper

    def delete(self, *a, **k):
        def _wrapper(f):
            return self.router.delete(*a, **k)(self.build(f))
        return _wrapper
