from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PullRequest(Base):
    __tablename__ = 'pull_request'

    id = Column(Integer, autoincrement=True, primary_key=True)
    pr_id = Column(String(255), index=True)
    rpm_name = Column(String(255))
    is_rpm_new = Column(Boolean)
