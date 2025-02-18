from __future__ import annotations

import secrets
from typing import Any

import _pickle as pickle
from redis.asyncio import Redis
from apphelpers.errors import InvalidSessionError

_SEP = ":"
session_key = ("session" + _SEP).__add__

rev_lookup_prefix = f"uid{_SEP}"


def rev_lookup_key(uid, site_ctx=None):
    return (
        f"{rev_lookup_prefix}{uid}{_SEP}{site_ctx}"
        if site_ctx
        else f"{rev_lookup_prefix}{uid}"
    )


THIRTY_DAYS = 30 * 24 * 60 * 60


class SessionDBHandler:
    def __init__(self, rconn_params):
        """
        rconn_params: redis connection parameters
        """
        self.rconn = Redis(**rconn_params)

    async def create(
        self,
        uid="",
        groups=None,
        site_groups=None,
        extras=None,
        ttl=THIRTY_DAYS,
        site_ctx=None,
    ):
        """
        groups: list
        site_groups: dict
        extras (dict): each key-value pair of extras get stored into hset
        site_ctx: int (session is only applicable for bound site_id)
        """
        if uid:
            sid = await self.uid2sid(uid, site_ctx)
            if sid:
                return sid

        sid = secrets.token_urlsafe()
        key = session_key(sid)

        if groups is None:
            groups = []
        session_dict = {
            "uid": uid,
            "groups": groups,
            "site_groups": site_groups,
            "site_ctx": site_ctx,
        }
        if extras:
            session_dict.update(extras)
        session = {k: pickle.dumps(v) for k, v in session_dict.items()}
        await self.rconn.hset(key, mapping=session)

        if uid:
            rev_key = rev_lookup_key(uid, site_ctx)
            await self.rconn.setex(rev_key, value=sid, time=ttl)
        await self.rconn.expire(key, ttl)
        return sid

    async def exists(self, sid):
        return await self.rconn.exists(session_key(sid))

    async def get(self, sid, keys=[]) -> dict[str, Any]:
        s_values = await self.rconn.hgetall(session_key(sid))
        if not s_values:
            raise InvalidSessionError()
        session = {k.decode(): pickle.loads(v) for k, v in s_values.items()}
        if keys:
            session = {k: session.get(k, None) for k in keys}
        return session

    async def get_attribute(self, sid, attribute):
        value = await self.rconn.hget(session_key(sid), attribute)
        return pickle.loads(value) if value else None

    async def uid2sid(self, uid, site_ctx=None):
        sid = await self.rconn.get(rev_lookup_key(uid, site_ctx))
        return sid.decode() if sid else None

    async def uid2bound_sids(self, uid):
        keys = await self.rconn.keys(rev_lookup_key(uid, "*"))
        return [(await self.rconn.get(key)).decode() for key in keys]

    async def uid2bound_site_ids(self, uid):
        keys = await self.rconn.keys(rev_lookup_key(uid, "*"))
        return [int(key.decode().split(_SEP)[2]) for key in keys]

    async def sid2uid(self, sid):
        session = await self.get(sid, ["uid"])
        return session["uid"]

    async def get_for(self, uid):
        sid = await self.uid2sid(uid)
        return await self.get(sid) if sid else None

    async def get_bound_sessions_for(self, uid):
        return [self.get(sid) for sid in await self.uid2bound_sids(uid)]

    # Same default ttl as `create` function
    async def extend_timeout(self, sid, ttl=THIRTY_DAYS):
        await self.rconn.expire(session_key(sid), ttl)
        uid = await self.sid2uid(sid)
        await self.rconn.expire(rev_lookup_key(uid), ttl)

    async def sid2uidgroups(self, sid):
        """
        => uid (int), groups (list)
        """
        session = await self.get(sid, ["uid", "groups"])
        return session["uid"], session["groups"]

    async def update(self, sid, keyvalues):
        sk = session_key(sid)
        keyvalues = {k: pickle.dumps(v) for k, v in list(keyvalues.items())}
        await self.rconn.hset(sk, mapping=keyvalues)

    async def update_for(self, uid, keyvalues):
        sid = await self.uid2sid(uid)
        return await self.update(sid, keyvalues) if sid else None

    async def update_attribute(self, sid, attribute, value):
        key = session_key(sid)
        await self.rconn.hset(key, attribute, pickle.dumps(value))
        return True

    async def resync(self, sid, keyvalues):
        removed_keys = list((await self.get(sid)).keys() - keyvalues.keys())
        await self.remove_from_session(sid, removed_keys)
        await self.update(sid, keyvalues)

    async def resync_for(self, uid, keyvalues, site_ctx=None):
        keyvalues["uid"] = uid
        keyvalues["site_ctx"] = site_ctx
        sid = await self.uid2sid(uid, site_ctx)
        return await self.resync(sid, keyvalues) if sid else None

    async def remove_from_session(self, sid, keys):
        sk = session_key(sid)
        if keys:
            await self.rconn.hdel(sk, *keys)
        return True

    async def destroy(self, sid, site_ctx=None):
        uid = (await self.sid2uidgroups(sid))[0]
        sk = session_key(sid)
        await self.rconn.delete(sk)
        await self.rconn.delete(rev_lookup_key(uid, site_ctx))
        return True

    async def destroy_for(self, uid, site_ctx=None):
        sid = await self.uid2sid(uid, site_ctx)
        return await self.destroy(sid, site_ctx) if sid else None

    async def destroy_all(self):
        keys = await self.rconn.keys(session_key("*"))
        if keys:
            await self.rconn.delete(*keys)
        keys = await self.rconn.keys(rev_lookup_prefix + "*")
        if keys:
            await self.rconn.delete(*keys)

    async def destroy_all_for_bound_site(self, site_ctx):
        keys = await self.rconn.keys(rev_lookup_key("*", site_ctx))
        if keys:
            sids = [session_key((await self.rconn.get(key)).decode()) for key in keys]
            if sids:
                await self.rconn.delete(*sids)
            await self.rconn.delete(*keys)

    async def destroy_bound_sessions_for(self, uid):
        keys = await self.rconn.keys(rev_lookup_key(uid, "*"))
        if keys:
            sids = [session_key((await self.rconn.get(key)).decode()) for key in keys]
            if sids:
                await self.rconn.delete(*sids)
            await self.rconn.delete(*keys)

    async def close(self):
        await self.rconn.aclose()
        return True
