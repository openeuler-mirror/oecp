import logging
from oecp.symbol_analyze.db_api import Api

logger = logging.getLogger('oecp')


class RpmController(object):
    def __init__(self, branch_name, db_password):
        self.db_api = Api(branch_name, db_password)
        self.branch_name = branch_name
        self.symbol_models = []
        self.pr_mappings = []

    def set_symbols(self, symbol_model):
        if symbol_model:
            self.symbol_models.append(symbol_model)

    def bulk_save_symbols(self, model):
        if self.symbol_models:
            self.db_api.bulk_save_objects(self.symbol_models)
            logger.info(f'A total of {len(self.symbol_models)} data records are inserted into the database '
                        f'{self.branch_name} table {model.__name__}.')
        else:
            logger.warning(f"No symbol_models records save to database: {self.branch_name}")

    def set_pr_mapping(self, pr_mapping):
        if pr_mapping:
            self.pr_mappings.append(pr_mapping)

    def bulk_save_pr_mappings(self, pr_id):
        if self.pr_mappings:
            self.db_api.bulk_save_objects(self.pr_mappings)
            logger.info(f'A total of {len(self.pr_mappings)} data records are inserted into the database '
                        f'{self.branch_name} table pullRequest with prId {pr_id}.')
        else:
            logger.warning(f"Not pr_mappings records save to database: {self.branch_name}")

    def query_pr_mappings_by_pr_id(self, pr_id=None):
        return self.db_api.query_pr_mappings_by_pr_id(pr_id)

    def delete_pr_mapping_by_pr_id(self, pr_id=None):
        return self.db_api.delete_pr_mapping_by_pr_id(pr_id)

    def query_symbol_by_filter(self, filters=None):
        return self.db_api.query_symbol(filters)

    def query_symbol_contains_so(self, filters=None):
        if not filters:
            filters = {}
        return self.db_api.select_symbol_contains_so(filters)

    def query_tmp_symbol(self, filters=None):
        if not filters:
            filters = {}
        return self.db_api.query_symbol_tmp(filters)

    def bulk_delete_datas(self, model, rpm_name=None):
        self.db_api.delete_by_rpm_name(model, rpm_name)
