import typing
import re

def full_path_builder(app_prefix: str, path: str):
    app_prefix = app_prefix.strip(' /')
    path = path.strip(' /')
    full = ''
    if app_prefix != '':
        full += '/' + app_prefix
    full = full.strip(' /')
    full = full.strip(' /')
    if path != '':
        full += '/' + path
    return '/' + full.strip(' /')


class BaseRoute:
    def __init__(self, scope, routes: typing.Dict = {}, prefix: str = '', package:str='', middlewares=None) -> None:
        if middlewares is None:
            middlewares = []
        self._routes = routes
        self._scope = scope
        self._app_prefix = prefix
        self._package = package
        self._middlewares = middlewares
        for m in ['POST', 'GET', 'PUT', 'OPTIONS', 'DELETE', 'WS']:
            if m not in self._routes:
                self._routes[m] = []

    def _add(self, path: str, controller: typing.Union[str, typing.Callable], method: str, middlewares=None, cache=None):
        if middlewares is None:
            middlewares = []
        full_path = full_path_builder(self._app_prefix, path)
        middlwrs = self._middlewares.copy()
        if self._package != '':
            controller = self._package + '.' + controller
        r={
            'path': full_path,
            'controller': controller,
            'middlewares': list(dict.fromkeys(middlwrs + middlewares))
        }
        if cache:
            r['cache']=cache
        self._routes[method].append(r)

    def all(self):
        return self._routes

    def response(self):
        method = self._scope['method']
        if method not in ['POST', 'GET', 'PUT', 'OPTIONS', 'DELETE', 'WS']:
            return False

        if self._scope['path'] != '/':
            self._scope['path'] = self._scope['path'].rstrip(' /')

        path = self._scope['path']

        for route in self._routes[method]:
            regex, params = build_path(route['path'])
            find = regex.search(path)
            args = {}
            if find:
                for param in params:
                    args[param] = find.group(param)

                return build(route, args)

        return False


class Router(BaseRoute):
    def __init__(self, scope=None, routes: typing.Dict = {}, prefix: str = '', package:str='', middlewares=None) -> None:
        if middlewares is None:
            middlewares = []
        super().__init__(scope, routes, prefix,package,middlewares)

    def get(self, path, controller, middlewares=None,cache=None):
        self._add(path, controller, 'GET', middlewares,cache)
        return self

    def post(self, path, controller, middlewares=None):
        self._add(path, controller, 'POST', middlewares)
        return self

    def put(self, path, controller, middlewares=None):
        self._add(path, controller, 'PUT', middlewares)
        return self

    def option(self, path, controller, middlewares=None):
        self._add(path, controller, 'OPTIONS', middlewares)
        return self

    def delete(self, path, controller, middlewares=None):
        self._add(path, controller, 'DELETE', middlewares)
        return self

    def ws(self, path, controller, middlewares=None):
        self._add(path, controller, 'WS', middlewares)
        return self

    def crud(self, path, controller, middlewares=None):
        self._add(path, controller+'@index', 'GET', middlewares)
        self._add(path, controller+'@store', 'POST', middlewares)
        self._add(path+'/{id}', controller+'@update', 'PUT', middlewares)
        self._add(path+'/{id}', controller+'@delete', 'DELETE', middlewares)
        return self


def build(route, args):
    controller = route['controller']
    res = {}
    res['path'] = route['path']
    res['args'] = args
    res['middlewares'] = route['middlewares']
    res['cache'] = route.get('cache',None)
    if type(controller) is str:
        res['controller'], res['func'] = controller.split('@')
    else:
        res['controller'] = None
        res['func'] = controller
    return res


def build_path(
        path: str,
        param_regex=re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[\s\S]*)?}")
) -> typing.Tuple[typing.Pattern, typing.List[str]]:
    path_regex = "^"
    idx = 0
    params = []
    for match in param_regex.finditer(path):
        param_name, name_regex = match.groups()

        path_regex += re.escape(path[idx: match.start()])
        if name_regex is not None:
            name_regex = name_regex.lstrip(':')
            path_regex += f"(?P<{param_name}>{name_regex})"
        else:
            path_regex += f"(?P<{param_name}>[^/]+)"

        params.append(param_name)
        idx = match.end()

    path_regex += re.escape(path[idx:]) + "$"
    return re.compile(path_regex), params
