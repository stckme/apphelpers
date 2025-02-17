from collections import namedtuple

import pytest

import apphelpers.async_sessions as sessionslib
from apphelpers.errors import InvalidSessionError


Session = namedtuple("Session", ["uid", "groups", "k", "v"])


class data:
    session = Session(987651, ["admin", "member"], "foo", "bar")
    session_email = "noone@example.com"
    site_ctx = 123


@pytest.mark.anyio
class TestSessions:

    @pytest.fixture(autouse=True)
    async def setup_class(self, sessionsdb: sessionslib.SessionDBHandler):
        await sessionsdb.destroy_all()

    async def test_create(self, sessionsdb: sessionslib.SessionDBHandler):
        # test create
        d = dict(
            uid=data.session.uid,
            groups=data.session.groups,
            extras=dict(email=data.session_email),
        )
        sid = await sessionsdb.create(**d)
        assert len(sid) == 43
        sid_new = await sessionsdb.create(data.session.uid, data.session.groups)
        assert sid == sid_new == await sessionsdb.uid2sid(d["uid"])
        assert await sessionsdb.uid2bound_sids(d["uid"]) == []

        d = dict(
            uid=data.session.uid,
            groups=data.session.groups,
            extras=dict(email=data.session_email),
            site_ctx=data.site_ctx,
        )
        bound_sid = await sessionsdb.create(**d)
        assert bound_sid != sid
        assert bound_sid == await sessionsdb.uid2sid(d["uid"], data.site_ctx)
        assert await sessionsdb.uid2bound_sids(d["uid"]) == [bound_sid]
        assert await sessionsdb.exists(bound_sid)
        assert await sessionsdb.uid2bound_site_ids(d["uid"]) == [data.site_ctx]

        await sessionsdb.destroy_all_for_bound_site(data.site_ctx)
        assert not await sessionsdb.exists(bound_sid)

        d = dict(
            uid=data.session.uid,
            groups=data.session.groups,
            extras=dict(email=data.session_email),
            site_ctx=data.site_ctx,
        )
        bound_sid = await sessionsdb.create(**d)
        assert bound_sid != sid
        assert bound_sid == await sessionsdb.uid2sid(d["uid"], data.site_ctx)
        assert await sessionsdb.uid2bound_sids(d["uid"]) == [bound_sid]
        assert await sessionsdb.exists(bound_sid)

        await sessionsdb.destroy_bound_sessions_for(data.session.uid)
        assert not await sessionsdb.exists(bound_sid)

    async def test_update(self, sessionsdb: sessionslib.SessionDBHandler):
        d = dict(
            uid=data.session.uid,
            groups=data.session.groups,
            extras=dict(email=data.session_email),
        )
        sid = await sessionsdb.create(**d)

        k, v = data.session.k, data.session.v
        await sessionsdb.update(sid, {k: v})
        d = await sessionsdb.get(sid)
        assert d[k] == v
        assert d["email"] == data.session_email
        await sessionsdb.remove_from_session(sid, [k])
        d = await sessionsdb.get(sid)
        assert k not in d

    async def test_resync(self, sessionsdb: sessionslib.SessionDBHandler):
        d = dict(
            uid=data.session.uid,
            groups=data.session.groups,
            extras=dict(email=data.session_email),
        )
        sid = await sessionsdb.create(**d)

        k, v = data.session.k, data.session.v
        await sessionsdb.update(sid, {k: v})
        d = await sessionsdb.get(sid)
        assert d[k] == v

        d = dict(
            uid=data.session.uid,
            groups=data.session.groups,
            extras=dict(email=data.session_email),
        )
        await sessionsdb.resync(sid, d)
        d = await sessionsdb.get(sid)
        assert k not in d

        await sessionsdb.destroy(sid)
        with pytest.raises(InvalidSessionError):
            await sessionsdb.get(sid)

    async def test_session_lookup(self, sessionsdb: sessionslib.SessionDBHandler):
        uids = range(10000, 10010)
        groups = ["grp1", "grp2"]
        for uid in uids:
            sid = await sessionsdb.create(uid, groups)
            assert (await sessionsdb.sid2uidgroups(sid)) == (uid, groups)
            await sessionsdb.destroy(sid)
            with pytest.raises(InvalidSessionError):
                await sessionsdb.get(sid)
