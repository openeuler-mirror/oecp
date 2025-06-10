import os
import logging
import configparser
logger = logging.getLogger('oecp')


class Config(object):
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.config = self.set_config(config_file)

    def set_config(self, config_file):
        if not config_file:
            config_file = os.path.realpath(os.path.join(os.path.dirname(__file__), "../conf/oecp.conf"))
        config = configparser.ConfigParser()
        config.read(config_file)
        return config

    def get_config(self, section, key, default=''):
        try:
            value = self.config.get(section, key)
        except configparser.NoSectionError:
            logger.warning(f"config file: {self.config_file} has no section: {section}")
            value = default
        except configparser.NoOptionError:
            logger.warning(f"config file: {self.config_file} section: {section} has no key:{key}")
            value = default
        return value
