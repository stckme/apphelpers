from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from converge import settings
from requests.exceptions import HTTPError

if settings.get("HONEYBADGER_API_KEY"):
    from honeybadger.utils import filter_dict


def phony(f):
    return f


@dataclass
class User:
    sid: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    groups: List[str] = field(default_factory=list)
    email: Optional[str] = None
    mobile: Optional[str] = None
    site_groups: Dict[int, int] = field(default_factory=dict)
    site_ctx: Optional[int] = None

    def to_dict(self):
        return asdict(self)

    def __bool__(self):
        return self.id is not None


def notify_honeybadger(honeybadger, error, func, args, kwargs):
    try:
        honeybadger.notify(
            error,
            context={
                "func": func.__name__,
                "args": args,
                "kwargs": filter_dict(copy.deepcopy(kwargs), settings.HB_PARAM_FILTERS),
            },
        )
    except HTTPError as e:
        if e.response.status_code == 403:
            # Ignore 403 Forbidden errors. We get alerted by HB anyway.
            pass
        else:
            raise e
