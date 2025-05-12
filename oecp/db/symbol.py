from sqlalchemy import Column, String, Text, Integer, VARCHAR
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Symbol(Base):
    __tablename__ = 'symbol'

    id = Column(Integer, autoincrement=True, primary_key=True)
    rpm_name = Column(String(255), index=True)
    so_name = Column(String(255))
    u_symbol_table = Column(VARCHAR(600), index=True)
    association_so_name = Column(Text)
