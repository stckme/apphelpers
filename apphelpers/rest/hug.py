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

    def map_resource(self, url, resource=None, handlers=None, id_field='id'):
        if resource:
            raise NotImplementedError("Resource not supported yet")

        collection_url = (self.urls_prefix + url) if not url.startswith('/') else url
        resource_url = collection_url + '{' + id_field + '}'

        assert isinstance(handlers, (list, tuple)), "handlers should be list or tuple"
        get_collection, add_resource, replace_resource, get_resource, update_resource, delete_resource = handlers

        if get_collection:
            self.get(collection_url)(get_collection)
        if add_resource:
            self.post(collection_url)(add_resource)
        if replace_resource:
            self.put(resource_url)(replace_resource)
        if get_resource:
            # get_resource_wrapped = get_or_not_found(get_resource)
            self.get(resource_url)(get_resource)
        if update_resource:
            self.patch(resource_url)(update_resource)
        if delete_resource:
            self.delete(resource_url)(delete_resource)
