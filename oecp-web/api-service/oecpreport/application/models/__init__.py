#!/usr/bin/python3


class BaseModel(object):
    def exists(self, db):
        _self = db.session.query(self.__class__).filter_by(id=self.id).first()
        if not _self:
            _self = self
        return _self

    @property
    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
