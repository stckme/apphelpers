import secrets
import _pickle as pickle
import redis
import hug

import apphelpers.context as context

from apphelpers.errors import InvalidSessionError


_SEP = ':'
session_key = ('session' + _SEP).__add__

rev_lookup_prefix = 'uid' + _SEP
rev_lookup_key = lambda uid: rev_lookup_prefix + str(uid)


class SessionDBHandler:

    def __init__(self, rconn_params):
        """
        rconn_params: redis connection parameters
        """
        self.rconn = redis.Redis(**rconn_params)

    def create(self, uid='', groups=None, extras=None, ttl=(30 * 24 * 60 * 60)):
        """
        groups: list
        extras (dict): each key-value pair of extras get stored into hset
        """
        if uid:
            sid = self.uid2sid(uid)
            if sid:
                return sid

        sid = secrets.token_urlsafe()
        key = session_key(sid)

        session_dict = {'uid': uid, 'groups': groups or []}
        if extras:
            session_dict.update(extras)
        session = {k: pickle.dumps(v) for k, v in session_dict.items()}
        self.rconn.hmset(key, session)

        if uid:
            rev_key = rev_lookup_key(uid)
            self.rconn.setex(rev_key, value=sid, time=ttl)
        self.rconn.expire(key, ttl)
        return sid

    def exists(self, sid):
        return self.rconn.exists(session_key(sid))

    def get(self, sid, keys=[]):
        s_values = self.rconn.hgetall(session_key(sid))
        if not s_values:
            raise InvalidSessionError()
        session = {k.decode(): pickle.loads(v) for k, v in s_values.items()}
        if keys:
            session = {k: session.get(k, None) for k in keys}
        return session

    def get_attribute(self, sid, attribute):
        value = self.rconn.hget(session_key(sid), attribute)
        return pickle.loads(value) if value else None

    def uid2sid(self, uid):
        sid = self.rconn.get(rev_lookup_key(uid))
        return sid.decode() if sid else None

    def get_for(self, uid):
        sid = self.uid2sid(uid)
        return self.get(sid) if sid else None

    def sid2uidgroups(self, sid):
        """
        => uid (int), groups (list)
        """
        session = self.get(sid, ['uid', 'groups'])
        return session['uid'], session['groups']

    def update(self, sid, keyvalues):
        sk = session_key(sid)
        keyvalues = {k: pickle.dumps(v) for k, v in list(keyvalues.items())}
        self.rconn.hmset(sk, keyvalues)

    def update_for(self, uid, keyvalues):
        sid = self.uid2sid(uid)
        return self.update(sid, keyvalues) if sid else None

    def update_attribute(self, sid, attribute, value):
        key = session_key(sid)
        self.rconn.hset(key, attribute, pickle.dumps(value))
        return True

    def remove_from_session(self, sid, keys):
        sk = session_key(sid)
        self.rconn.hdel(sk, keys)
        return True

    def destroy(self, sid):
        uid = self.sid2uidgroups(sid)[0]
        sk = session_key(sid)
        self.rconn.delete(sk)
        self.rconn.delete(rev_lookup_key(uid))
        return True

    def destroy_for(self, uid):
        sid = self.uid2sid(uid)
        return self.destroy(sid) if sid else None

    def destroy_all(self):
        keys = self.rconn.keys(session_key('*'))
        self.rconn.delete(*keys)
        keys = self.rconn.keys(rev_lookup_prefix + '*')
        self.rconn.delete(*keys)


def whoami(user: hug.directives.user):
    return user.to_dict()
#whoami.login_required = True
