# -*- coding: utf-8 -*-
from collections import namedtuple

import pytest

import apphelpers.sessions as sessionslib
import settings
from apphelpers.errors import InvalidSessionError

sessiondb_conn = dict(
    host=settings.SESSIONSDB_HOST,
    port=settings.SESSIONSDB_PORT,
    password=settings.SESSIONSDB_PASSWD,
    db=settings.SESSIONSDB_NO,
)
sessionsdb = sessionslib.SessionDBHandler(sessiondb_conn)
sessionsdb.destroy_all()


class data:
    pass


class state:
    pass


Session = namedtuple("Session", ["uid", "groups", "k", "v"])
data.session = Session(987651, ["admin", "member"], "foo", "bar")
data.session_email = "noone@example.com"
data.site_ctx = 123

# uid, groups, k, v = 987651, ['admin', 'member'], 'foo', 'bar'


def test_create():
    d = dict(
        uid=data.session.uid,
        groups=data.session.groups,
        extras=dict(email=data.session_email),
    )
    sid = sessionsdb.create(**d)
    assert len(sid) == 43
    sid_new = sessionsdb.create(data.session.uid, data.session.groups)
    assert sid == sid_new == sessionsdb.uid2sid(d["uid"])
    state.sid = sid
    assert sessionsdb.uid2bound_sids(d["uid"]) == []

    d = dict(
        uid=data.session.uid,
        groups=data.session.groups,
        extras=dict(email=data.session_email),
        site_ctx=data.site_ctx,
    )
    bound_sid = sessionsdb.create(**d)
    assert bound_sid != sid
    assert bound_sid == sessionsdb.uid2sid(d["uid"], data.site_ctx)
    assert sessionsdb.uid2bound_sids(d["uid"]) == [bound_sid]
    assert sessionsdb.exists(bound_sid)
    assert sessionsdb.uid2bound_site_ids(d["uid"]) == [data.site_ctx]

    sessionsdb.destroy_all_for_bound_site(data.site_ctx)
    assert not sessionsdb.exists(bound_sid)

    d = dict(
        uid=data.session.uid,
        groups=data.session.groups,
        extras=dict(email=data.session_email),
        site_ctx=data.site_ctx,
    )
    bound_sid = sessionsdb.create(**d)
    assert bound_sid != sid
    assert bound_sid == sessionsdb.uid2sid(d["uid"], data.site_ctx)
    assert sessionsdb.uid2bound_sids(d["uid"]) == [bound_sid]
    assert sessionsdb.exists(bound_sid)

    sessionsdb.destroy_bound_sessions_for(data.session.uid)
    assert not sessionsdb.exists(bound_sid)


def test_update():
    sid = state.sid
    k, v = data.session.k, data.session.v
    sessionsdb.update(sid, {k: v})
    d = sessionsdb.get(sid)
    assert d[k] == v
    assert d["email"] == data.session_email
    sessionsdb.remove_from_session(sid, [k])
    d = sessionsdb.get(sid)
    assert k not in d


def test_resync():
    sid = state.sid
    k, v = data.session.k, data.session.v
    sessionsdb.update(sid, {k: v})
    d = sessionsdb.get(sid)
    assert d[k] == v

    d = dict(
        uid=data.session.uid,
        groups=data.session.groups,
        extras=dict(email=data.session_email),
    )
    sessionsdb.resync(sid, d)
    d = sessionsdb.get(sid)
    assert k not in d


def test_delete():
    sessionsdb.destroy(state.sid)
    with pytest.raises(InvalidSessionError):
        sessionsdb.get(state.sid)


def test_session_lookups():
    uids = range(10000, 10010)
    groups = ["grp1", "grp2"]
    for uid in uids:
        sid = sessionsdb.create(uid, groups)
        assert sessionsdb.sid2uidgroups(sid) == (uid, groups)
        sessionsdb.destroy(sid)
        with pytest.raises(InvalidSessionError):
            sessionsdb.get(sid)


def test_site_bound_sessions():
    uid = 100000
    site1_id = 200000
    site2_id = 200001
    sid = sessionsdb.create(uid=uid)
    bound_sid1 = sessionsdb.create(uid=uid, site_ctx=site1_id)
    bound_sid2 = sessionsdb.create(uid=uid, site_ctx=site2_id)

    assert sid == sessionsdb.uid2sid(uid)
    assert bound_sid1 == sessionsdb.uid2sid(uid, site1_id)
    assert bound_sid2 == sessionsdb.uid2sid(uid, site2_id)
    assert set(sessionsdb.uid2bound_site_ids(uid)) == {site1_id, site2_id}
    assert set(sessionsdb.uid2bound_sids(uid)) == {bound_sid1, bound_sid2}

    sessionsdb.rconn.delete(sessionslib.session_key(bound_sid1))
    sessionsdb.rconn.delete(sessionslib.rev_lookup_key(uid, site1_id))

    assert set(sessionsdb.uid2bound_site_ids(uid)) == {site2_id, site1_id}
    assert (
        sessionsdb.resync_for(
            uid, {"uid": uid, "site_ctx": site1_id}, site_ctx=site1_id
        )
        is False
    )
    assert set(sessionsdb.uid2bound_site_ids(uid)) == {site2_id}
    assert set(sessionsdb.uid2bound_sids(uid)) == {bound_sid2}

    sessionsdb.destroy_for(uid, site_ctx=site2_id)
    assert set(sessionsdb.uid2bound_site_ids(uid)) == set()
    assert not sessionsdb.rconn.exists(sessionslib.ctx_rev_lookup_key(uid))

    bound_sid1 = sessionsdb.create(uid=uid, site_ctx=site1_id)
    sessionsdb.destroy_all_for_bound_site(site1_id)
    assert not sessionsdb.exists(bound_sid1)
