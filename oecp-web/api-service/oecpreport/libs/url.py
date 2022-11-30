#!/usr/bin/python3
from libs.exceptions import ContentNoneException
import importlib


def module_string(module_path, import_module=True):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.

    Args:
        module_path:Module path
    """
    try:
        if not import_module:
            module_path, class_name = module_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % module_path) from err

    module = importlib.import_module(module_path)
    if import_module:
        return module
    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError(
            'Module "%s" does not define a "%s" attribute/class'
            % (module_path, class_name)
        ) from err


def include(arg):
    """
    加入蓝图和api服务
    :param arg:注册的蓝图和api，以及url的前缀.例如：include('test_module','/api/v1.0')
    """
    url_prefix = None
    if isinstance(arg, tuple):
        # Callable returning a namespace hint
        try:
            urlconf_module, url_prefix = arg
        except ValueError:
            raise ContentNoneException(
                "Passing a %d-tuple to include() is not supported. Pass a "
                "2-tuple containing the list of patterns and url_prefix" % len(arg)
            )
    else:
        urlconf_module = arg

    if isinstance(urlconf_module, str):
        urlconf_module = module_string(urlconf_module)
    try:
        blue_print = getattr(urlconf_module, "blue_print")
        api = getattr(urlconf_module, "api")
        urls = getattr(urlconf_module, "urls", [])

    except AttributeError:
        raise RuntimeError(
            "Blueprints failed to register. Please check whether the imported module "
            "has properties such as BLUE_print and API"
        )
    # Register the URL and attempt to register into the Blueprint API
    if isinstance(urls, (tuple, list)):
        try:
            for view, url in urls:
                if isinstance(url, str):
                    url = (url,)
                api.add_resource(view, *(url_prefix + _url for _url in url))
        except ValueError:
            raise RuntimeError(
                "A registered route needs to be a tuple that can be iterated over,"
                " and the tuple can only contain View and URL addresses"
            )
    return (blue_print, api)
