import inspect
import traceback
from os import walk
import json

from renus.core.exception import debug_response
from renus.core.websockets import WebSocket
from renus.core.config import Config
from renus.core.routing import Router
from renus.core.request import Request
from renus.core.response import Response, TextResponse, JsonResponse
from renus.core.middleware import Middleware


class App:
    def __init__(self, lifespan=None,
                 on_startup=None,
                 on_shutdown=None) -> None:
        self.load_configs()
        self.load_configs()
        self.on_startup = [] if on_startup is None else list(on_startup)
        self.on_shutdown = [] if on_shutdown is None else list(on_shutdown)

        async def default_lifespan(app):
            await self.startup()
            yield
            await self.shutdown()

        self.lifespan_context = default_lifespan if lifespan is None else lifespan

    async def __call__(self, scope, receive, send) -> None:
        scope["app"] = self
        assert scope["type"] in ("http", "websocket", "lifespan")
        self.scope = scope

        if scope["type"] == "http":
            await self.http(send, receive)

        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)

        if scope["type"] == "websocket":
            await self.websocket(scope, receive, send)

    async def websocket(self, scope, receive, send) -> None:
        self.scope = scope
        self.scope["method"] = 'WS'
        self.send = send
        self.receive = receive
        self.ws = WebSocket(self.scope, self.receive, self.send)

        try:
            res = self.load_routes()

            setattr(self.ws, 'route', res)
            if not res:
                await self.ws.close(1004)
            else:
                middlewares = Config('app', self.ws).get('middlewares_ws', [])
                middlewares = middlewares + res['middlewares']
                passed = Middleware(self.ws, middlewares).next()

                if passed is not True:
                    await self.ws.close(1003)
                    return

                if res["controller"] is not None:
                    controller = import_by_string(res["controller"])
                    method = getattr(controller, res['func'])
                else:
                    method = res['func']

                res['args']['ws'] = self.ws

                await method(**res['args'])

        except Exception as exc:
            debug_response(exc)
            if Config('app',self.ws).get('env', 'local') == 'local':
                raise

    async def lifespan(self, scope, receive, send) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        first = True
        app = scope.get("app")
        await receive()
        try:
            if inspect.isasyncgenfunction(self.lifespan_context):
                async for item in self.lifespan_context(app):
                    assert first, "Lifespan context yielded multiple times."
                    first = False
                    await send({"type": "lifespan.startup.complete"})
                    await receive()
            else:
                for item in self.lifespan_context(app):  # type: ignore
                    assert first, "Lifespan context yielded multiple times."
                    first = False
                    await send({"type": "lifespan.startup.complete"})
                    await receive()
        except BaseException:
            if first:
                exc_text = traceback.format_exc()
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            if Config('app').get('env', 'local') == 'local':
                raise
        else:
            await send({"type": "lifespan.shutdown.complete"})

    async def http(self, send, receive):
        self.scope["method"] = self.scope["method"].upper()
        self.send = send
        self.receive = receive
        self.request = Request(self.scope, self.receive)

        if self.scope["method"] in ['POST', 'PUT', 'DELETE']:
            setattr(self.request, 'inputs', await Request(self.scope, self.receive).form())

        try:
            await self.view()
        except Exception as exc:
            from renus.core.exception import debug_response
            debug = debug_response(exc)
            await self.result(JsonResponse(*debug))
            if Config('app',self.request).get('env', 'local') == 'local':
                raise

    async def startup(self) -> None:
        """
        Run any `.on_startup` event handlers.
        """
        print('application startup')
        for handler in self.on_startup:
            if inspect.isasyncgenfunction(handler):
                await handler()
            else:
                handler()

    async def shutdown(self) -> None:
        """
        Run any `.on_shutdown` event handlers.
        """
        print('application shutdown')
        for handler in self.on_shutdown:
            if inspect.isasyncgenfunction(handler):
                await handler()
            else:
                handler()

    async def view(self):
        res = self.load_routes()

        setattr(self.request, 'route', res)
        if not res:
            await self.result(TextResponse('not_found', 404))
        else:
            middlewares = Config('app', self.request).get('middlewares', [])
            middlewares = middlewares + res['middlewares']
            passed = Middleware(self.request, middlewares).next()

            if passed is not True and self.request.method != 'OPTIONS':
                await self.result(JsonResponse(passed, 403))
            else:
                if res["controller"] is not None:
                    controller = import_by_string(res["controller"])
                    method = getattr(controller, res['func'])
                else:
                    method = res['func']

                if 'request' in method.__code__.co_varnames:
                    res['args']['request'] = self.request

                if inspect.iscoroutinefunction(method):
                    await self.result(await method(**res['args']))
                else:
                    await self.result(method(**res['args']))

    async def result(self, response):
        if not isinstance(response, Response):
            response = TextResponse(response)
        await response(self.scope, self.receive, self.send)

    def load_routes(self):
        if not hasattr(self, "routes"):
            import routes.index
            self.routes = Router().all()

        return Router(self.scope, self.routes).response()

    def load_configs(self):
        self.configs = {}
        files = []

        for (dirpath, dirnames, filenames) in walk('config'):
            files.extend(filenames)
            break
        for file in files:
            with open(f'config/{file}') as json_file:
                self.configs[file.replace('.json', '')] = json.load(json_file)


def import_by_string(controller: str):
    full_path = f'app.http.{controller}.controller'
    c = controller.split('.')
    return getattr(__import__(full_path, fromlist=['']), c[-1].title().replace('_', '') + 'Controller')()
