#!/usr/bin/python3
"""
Description: Simple encapsulation of sqlalchemy orm framework operation database
Class: DBHelper
"""
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from .exceptions import ContentNoneException
from .conf import settings


__all__ = ["DataBase"]


class Mysql:
    """
    Description: mysql database connection related operations
    Attributes:
        user_name: Database connection username
        password: Database connection password
        host: Remote server address
        port: Port
        database: Operational database name
        connection_type: Database connection type
    """

    def __init__(
        self,
        user_name=None,
        password=None,
        host=None,
        port=None,
        database=None,
        **kwargs
    ):
        super(Mysql, self).__init__()
        self.user_name = user_name or settings.db_account
        self.password = password or settings.db_password
        self.host = host or settings.db_host
        self.port = port or settings.db_port
        self.database = database or settings.database
        self.connection_type = "mysql+pymysql"

    def create_database_engine(self):
        """
        Description: Create a database connection object
        Args:

        Returns:
        Raises:
            DisconnectionError: A disconnect is detected on a raw DB-API connection.

        """
        if not all(
            [self.user_name, self.password, self.host, self.port, self.database]
        ):
            raise DisconnectionError(
                "A disconnect is detected on a raw DB-API connection"
            )
        # create connection object
        engine = create_engine(
            URL(
                **{
                    "database": self.database,
                    "username": self.user_name,
                    "password": self.password,
                    "host": self.host,
                    "port": self.port,
                    "drivername": self.connection_type,
                }
            ),
            encoding="utf-8",
            convert_unicode=True,
            echo=True,
        )
        return engine


class DataBase:
    """
    Description: Database connection, operation public class
    Attributes:
        user_name: Username
        password: Password
        host: Remote server address
        port: Port
        db_name: Database name
        connection_type: Database type
        session: Session
    """

    # The base class inherited by the data model
    BASE = declarative_base()
    _lock = threading.Lock()
    engine = None

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not hasattr(cls, "__instance"):
                cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(
        self,
        user_name=None,
        password=None,
        host=None,
        port=None,
        db_name=None,
        **kwargs
    ):
        """
        Description: Class instance initialization

        """
        self._mysql = Mysql(
            user_name=user_name,
            password=password,
            host=host,
            port=port,
            database=db_name,
            **kwargs
        )
        if self.engine is None:
            self.engine = self._mysql.create_database_engine()
        self.session = None

    def create_engine(self):
        """
        Create related database engine connections
        """
        session = sessionmaker()
        try:
            session.configure(bind=self.engine)
        except DisconnectionError:
            raise
        else:
            self.session = session()
        return self

    def close_session(self):
        """
        关闭session回话机制
        """
        if self.session is None:
            raise SQLAlchemyError("The session no longer exists .")
        self.session.close()

    def __enter__(self):
        """
        Description: functional description:Create a context manager for the database connection
        Args:

        Returns:
            Class instance
        Raises:

        """

        database_engine = self.create_engine()
        return database_engine

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Description: functional description:Release the database connection pool
                     and close the connection
        Returns:
            exc_type: Abnormal type
            exc_val: Abnormal value
            exc_tb: Abnormal table
        Raises:

        """
        if isinstance(exc_type, (AttributeError)):
            raise SQLAlchemyError(exc_val)
        self.session.close()

    @classmethod
    def create_all(cls, db_name):
        """
        functional description:Create all database tables
        :param db_name: Database name
        """
        cls.BASE.metadata.create_all(bind=cls(db_name=db_name).engine)

    def add(self, entity):
        """
        Description: Insert a single data entity
        Args:
            entity: Data entity
        Return:
            If the addition is successful, return the corresponding entity, otherwise return None
        Raises:
            ContentNoneException: An exception occurred while content is none
            SQLAlchemyError: An exception occurred while creating the database
        """

        if entity is None:
            raise SQLAlchemyError("The added entity content cannot be empty")
        if hasattr(entity, "id") and entity.id == 0:
            entity.id = None
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity, entity_dict):
        """
        Description: Insert a single data entity
        :param entity_dict: 需要更新的字典
        :param entity: 待更新的实体
        Return:
            If the addition is successful, return the corresponding entity, otherwise return None
        Raises:
            ContentNoneException: An exception occurred while content is none
            SQLAlchemyError: An exception occurred while creating the database
        """

        if entity is None:
            raise SQLAlchemyError("The added entity content cannot be empty")
        if not isinstance(entity_dict, dict):
            raise TypeError("entity_dict should be a dict.")
        for key, val in entity_dict.items():
            setattr(entity, key, val)

        # self.session.commit()
        self.session.flush()
        return entity

    def batch_add(self, dicts, model):
        """
        Description:tables for adding databases in bulk
        Args:
            dicts:Entity dictionary data to be added
            model:Solid model class
        Returns:

        Raises:
            TypeError: An exception occurred while incoming type does not meet expectations
            SQLAlchemyError: An exception occurred while creating the database
        """

        if model is None:
            raise ContentNoneException("solid model must be specified")

        if not dicts:
            raise ContentNoneException("The inserted data content cannot be empty")

        if not isinstance(dicts, list):
            raise TypeError(
                "The input for bulk insertion must be a dictionary"
                "list with the same fields as the current entity"
            )
        self.session.execute(model.__table__.insert(), dicts)

    def delete(self, entity):
        """
        Description: 删除实体
        Args:
            entity: Data entity
        Return:
            If the addition is successful, return the corresponding entity, otherwise return None
        Raises:
            ContentNoneException: An exception occurred while content is none
            SQLAlchemyError: An exception occurred while creating the database
        """
        if entity is None:
            raise SQLAlchemyError("The deleted entity content cannot be empty")
        self.session.delete(entity)
        self.session.flush()
        return entity

    def batch_delete(self, dicts, model):
        """
        Description:tables for delete databases in bulk
        """

        if model is None:
            raise ContentNoneException("solid model must be specified")

        if not dicts:
            raise ContentNoneException("The delete data content cannot be empty")

        if not isinstance(dicts, list):
            raise TypeError(
                "The input for bulk insertion must be a dictionary"
                "list with the same fields as the current entity"
            )
        try:
            # self.session.execute(model.__table__.delete(), dicts)
            for item in dicts:
                self.session.delete(item)
        except SQLAlchemyError as sql_error:
            self.session.rollback()
            raise SQLAlchemyError(sql_error)
        else:
            self.session.commit()

    def to_dict(self, rows, single=False):
        if not rows:
            return None if single else []

        if single:
            return dict(zip(rows.keys(), rows))

        return [dict(zip(row.keys(), row)) for row in rows]
