def check(middleware:str,request):
    middleware=middleware.split(':')
    cls=import_by_string(middleware[0])()
    return cls.handle(request,*middleware[1:])


def import_by_string(middleware):
    return getattr(__import__(f"app.middlewares.{middleware}", fromlist=['']),middleware.title())

class Middleware:
    def __init__(self, request, middlewares=None) -> None:
        if middlewares is None:
            middlewares = []
        self.middlewares = middlewares
        self.request = request

    def next(self):
        for middleware in self.middlewares:
            handle=check(middleware,self.request)
            if handle.get('pass',False) is not True:
                return {'middleware':middleware,'msg':handle.get('msg',None)}

        return True
