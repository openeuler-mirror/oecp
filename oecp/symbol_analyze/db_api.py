import logging
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from oecp.db.symbol import Base as symbol_base
from oecp.db.symbol import Symbol
from oecp.db.symbol_temporary import Base as symbol_tmp_base
from oecp.db.symbol_temporary import SymbolTemporary
from oecp.db.pull_request import Base as pull_request_base
from oecp.db.pull_request import PullRequest
from oecp.utils.config import Config

logger = logging.getLogger('oecp')


class Api(object):
    def __init__(self, database_name, db_password):
        self.session = self.get_session(database_name, db_password)

    def get_session(self, database_name, db_password):
        config = Config()
        user = config.get_config('database', 'dbuser', 'root')
        ip = config.get_config('database', 'dbhost', '127.0.0.1')
        port = config.get_config('database', 'dbport', '3306')
        data_url = 'mysql+pymysql://%s:%s@%s:%s/%s?charset=utf8&autocommit=true' % \
                   (user, db_password, ip, port, database_name)
        try:
            engine = create_engine(data_url, connect_args={'connect_timeout': 60}, pool_recycle=3600)
            if not database_exists(engine.url):
                create_database(engine.url)
                symbol_base.metadata.create_all(engine)
                symbol_tmp_base.metadata.create_all(engine)
                pull_request_base.metadata.create_all(engine)

            db_session = sessionmaker(bind=engine)()
        except Exception as e:
            error_msg = "connect database error, ip={}, port={}, database={}, detail={}".format(ip, port,
                                                                                                 database_name, e)
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            return db_session

    def bulk_save_objects(self, object_list):
        try:
            self.session.bulk_save_objects(object_list)
        except Exception as e:
            self.session.rollback()
            error_msg = 'bulk save objects error!,detail: {}'.format(e)
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            self.session.commit()

    def query_symbol(self, filters=None, limit=None):
        if not filters:
            filters = {}
        query = self.session.query(Symbol)
        ret = self.query_by_filter(query, Symbol, filters, limit)
        return ret if ret else []

    def query_pr_mappings_by_pr_id(self, pr_id=None):
        query = self.session.query(PullRequest)
        if pr_id:
            query = query.filter(PullRequest.pr_id == pr_id)
        return query.all()

    def query_by_filter(self, query, model, filters=None, limit=None):
        if filters.get('rpm_name', None):
            query = query.filter(model.rpm_name == filters['rpm_name'])
        if filters.get('so_name', None):
            query = query.filter(model.so_name == filters['so_name'])
        if filters.get('u_symbol_table', None):
            query = query.filter(model.u_symbol_table == filters['u_symbol_table'])
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def select_symbol_contains_so(self, filters=None, limit=None):
        """
        select_symbol_mult_so
        :param session: db session
        :param filters: db filters
        :param limit: db limit
        :return:
        """
        if filters is None:
            filters = {}

        query = self.session.query(Symbol)

        if filters.get('u_symbol_table', None):
            query = query.filter(Symbol.u_symbol_table == filters['u_symbol_table'])
        if filters.get('association_so_name', None):
            query = query.filter(Symbol.association_so_name.contains(filters['association_so_name']))
        if limit is not None:
            query = query.limit(limit)

        return query.with_entities(Symbol.rpm_name, Symbol.so_name, Symbol.u_symbol_table,
                                   Symbol.association_so_name).distinct().all()

    def get_symbols_by_id(self, s_id):
        """
        get_symbols_by_id
        :param session: db session
        :param s_id: symbol id
        :return: db query results
        """
        results = self.query_symbol({"id": s_id})
        if not results:
            raise ValueError("The symbols data is not found by '%s'" % s_id)
        return results

    def update_symbol_object(self, symbol_ref, values):
        """
        update_symbols
        :param session: db session
        :param symbol_ref: db data
        :param values: db update values of symbol
        :return:
        """
        if 'rpm_name' in values:
            symbol_ref.rpm_name = values['rpm_name']
        if 'so_name' in values:
            symbol_ref.rpm_name = values['so_name']
        if 'u_symbol_table' in values:
            symbol_ref.rpm_name = values['u_symbol_table']
        symbol_ref.update(values)

        return symbol_ref

    def create_symbols(self, context, values):
        service_ref = Symbol()
        service_ref.update(values)
        try:
            service_ref.save(context.session)
        except Exception as e:
            raise ValueError("An exception occurred when adding symbols: '%s'" % e)
        return service_ref

    def query_count(self, model, filters=None):
        """
        query_count
        :param session: db session
        :param model: table model
        :return: count of table
        """
        if filters is None:
            filters = {}
        query = self.session.query(func.count(model.id))
        if filters.get('rpm_name', None):
            query = query.filter(model.rpm_name == filters['rpm_name'])
        count = query.scalar()
        return count if count else 0

    def query_symbol_tmp(self, filters=None):
        if not filters:
            filters = {}
        query = self.session.query(SymbolTemporary)
        ret = self.query_by_filter(query, SymbolTemporary, filters)
        return ret if ret else []

    def delete_by_rpm_name(self, model, rpm_name):
        try:
            self.session.query(model).filter(model.rpm_name == rpm_name).delete()
            self.session.commit()
            logger.info(f'RPM {rpm_name} deleted records from the table model {model.__name__}.')
        except Exception as e:
            self.session.rollback()
            raise ValueError("delete by rpm name error, mode:{}, rpm_name:{}, detail:{}".format(model, rpm_name, e))

    def delete_pr_mapping_by_pr_id(self, pr_id):
        try:
            query_result = self.session.query(PullRequest).filter(PullRequest.pr_id == pr_id)
            query_num = len(query_result.all())
            query_result.delete()
            self.session.commit()
            logger.info(f'A total of {query_num} records are deleted from the table pullRequest with prId {pr_id}.')
        except Exception as e:
            self.session.rollback()
            raise ValueError("delete pr mapping by pr id error, pr_id:{}, detail={}".format(pr_id, e))
