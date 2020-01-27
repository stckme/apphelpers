from enum import Enum


class globalgroups(Enum):
    privileged = 1
    others = 2
    forbidden = 3


class sitegroups(Enum):
    privileged = 11
    others = 12
    forbidden = 13
