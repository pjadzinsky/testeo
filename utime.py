import datetime
from dateutil import parser
import time
import calendar
import pytz


class utime(object):
    def __init__(self, datetime):
        self.datetime = datetime
        self.ensure_not_naive()

    @classmethod
    def from_timestamp(cls, t0):
        d = datetime.datetime.utcfromtimestamp(t0)
        d = pytz.utc.localize(d)
        return cls(d)

    @classmethod
    def from_iso(cls, t0_in_iso):
        datetime_obj = parser.parse(t0_in_iso)
        d = cls(datetime_obj)
        return d

    def isoformat(self):
        return self.datetime.isoformat()

    def ensure_not_naive(self):
        if self.datetime.tzinfo is not None and self.datetime.utcoffset() is not None:
            pass
        else:
            raise IOError

    def to_timestamp(self):
        return calendar.timegm(self.datetime.timetuple())
