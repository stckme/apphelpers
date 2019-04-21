# -*- coding: utf-8 -*-
from collections import namedtuple

from nose.tools import raises

import apphelpers.sessions as sessionslib
import settings

from apphelpers.errors import InvalidSessionError


sessiondb_conn = dict(host=settings.SESSIONSDB_HOST,
                      port=settings.SESSIONSDB_PORT,
                      password=settings.SESSIONSDB_PASSWD,
                      db=settings.SESSIONSDB_NO)
sessionsdb = sessionslib.SessionDBHandler(sessiondb_conn)


class data:
    pass


class state:
    pass


Session = namedtuple('Session', ['uid', 'groups', 'k', 'v'])
data.session = Session(987651, ['admin', 'member'], 'foo', 'bar')
data.session_email = 'noone@example.com'

#uid, groups, k, v = 987651, ['admin', 'member'], 'foo', 'bar'


def test_create():
    d = dict(uid=data.session.uid, groups=data.session.groups, extras=dict(email=data.session_email))
    sid = sessionsdb.create(**d)
    assert len(sid) == 43
    sid_new = sessionsdb.create(data.session.uid, data.session.groups)
    assert sid == sid_new
    state.sid = sid


def test_uodate():
    sid = state.sid
    k, v = data.session.k, data.session.v
    sessionsdb.update(sid, {k: v})
    d = sessionsdb.get(sid)
    assert d[k] == v
    assert d['email'] == data.session_email
    sessionsdb.remove_from_session(sid, k)
    d = sessionsdb.get(sid)
    assert k not in d


@raises(InvalidSessionError)
def test_delete():
    sessionsdb.destroy(state.sid)
    assert sessionsdb.get(state.sid)


def test_session_lookups():
    uids = range(10000, 10010)
    groups = ['grp1', 'grp2']
    for uid in uids:
        sid = sessionsdb.create(uid, groups)
        assert sessionsdb.sid2uidgroups(sid) == (uid, groups)
        sessionsdb.destroy(sid)
        raises(InvalidSessionError)(sessionsdb.get)(sid)
