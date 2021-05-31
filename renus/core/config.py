import json

from renus.core.request import Request


class Config:
    def __init__(self, name: str, request=None) -> None:
        if request is None or type(request) is not Request:
            with open(f'config/{name}.json') as json_file:
                self.config = json.load(json_file)
        else:
            self.config = request.app.configs[name]

    def get(self, name, default=None):
        if name in self.config:
            return self.config[name]
        if default is not None:
            return default
        raise RuntimeError(f'key: {name} not found.')
