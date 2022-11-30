#!/usr/bin/python3
import os
import configparser


DEFAULT_SETTINGS = {}


class PreloadingSettings:
    """
    The system default configuration file and the configuration
    file changed by the user are lazily loaded.
    """

    _setting_container = None

    def __init__(self) -> None:
        self._preloading()

    def _preloading(self):
        """
        Load the default configuration in the system and the related configuration
        of the user, and overwrite the default configuration items of the system
        with the user's configuration data
        """
        settings_file = os.environ.get("SETTINGS_FILE") or "/etc/oecpreport/conf.ini"
        if not settings_file:
            raise RuntimeError(
                "The system does not specify the user configuration"
                "that needs to be loaded: 'SETTINGS_FILE' ."
            )

        self._setting_container = Configs(settings_file)

    def __getattr__(self, name):
        """
        Return the value of a setting and cache it in self.__dict__
        """
        if self._setting_container is None:
            self._preloading()
        value = getattr(self._setting_container, name, None)
        self.__dict__[name] = value
        return value

    def __setattr__(self, name, value):
        """
        Set the configured value and re-copy the value cached in __dict__
        """
        if name is None:
            raise KeyError("The set configuration key value cannot be empty")
        if name == "_setting_container":
            self.__dict__.clear()
            self.__dict__["_setting_container"] = value
        else:
            self.__dict__.pop(name, None)
        if self._setting_container is None:
            self._preloading()
        setattr(self._setting_container, name, value)

    def __delattr__(self, name):
        """
        Delete a setting and clear it from cache if needed
        """
        if name is None:
            raise KeyError("The set configuration key value cannot be empty")

        if self._setting_container is None:
            self._preloading()
        delattr(self._setting_container, name)
        self.__dict__.pop(name, None)

    @property
    def config_ready(self):
        """
        Return True if the settings have already been configured
        """
        return self._setting_container is not None


class Configs:
    """
    The system's default configuration items and the user's
    configuration items are integrated
    """

    def __init__(self, conf_file):
        for config in DEFAULT_SETTINGS:
            setattr(self, config.lower(), DEFAULT_SETTINGS[config])
        self.conf_parser = self._init_conf_parse(conf=conf_file)
        self._parse_conf()

    def _init_conf_parse(self, conf):
        parser = configparser.RawConfigParser()
        parser.read(conf, encoding="utf-8")
        return parser

    def _set_conf_val(self, option):
        key, config_value = option

        if not config_value:
            return
        if config_value.isdigit():
            config_value = int(config_value)
        elif config_value.lower() in ("true", "false", "1", "0"):
            config_value = bool(config_value)

        setattr(self, key.lower(), config_value)

    def _parse_conf(self):
        sections = list(self.conf_parser.sections())
        while sections:
            section = sections.pop()
            for option in self.conf_parser.items(section):
                self._set_conf_val(option)


settings = PreloadingSettings()
