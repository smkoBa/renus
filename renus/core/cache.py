import os
from datetime import datetime, timedelta
import pickle

from renus.util.helper import hash_key


class Cache:
    def __init__(self) -> None:
        self.depth = 1

    def put(self, key, value, expire: int = 60):
        """
        add value by key to cache system
        :param key: key for value
        :param value: value that save by key
        :param expire: seconds to expire from now
        """
        expire = datetime.utcnow() + timedelta(seconds=expire)
        path = build_name(key, self.depth)
        self.create_if_not_exist(path, value, expire)
        self.add_to_list(path, expire)

    def get(self, key, default=None):
        path = build_name(key, self.depth)
        return self.read_key(path, default)['value']

    def expire(self, key, default=None):
        path = build_name(key, self.depth)
        return self.read_key(path, default)['expire']

    def delete(self, key):
        path = build_name(key, self.depth)
        return self.delete_file("storage/cache" + path)

    def delete_expired(self):
        from renus.core.log import Log
        filename = 'storage/cache/r/en/usl/ist'
        try:
            with open(filename, 'rb') as input:
                data = pickle.load(input)
        except Exception:
            data = {}
        res = {}
        n = 0
        for (key, expire) in data.items():
            if expire > datetime.utcnow():
                res[key] = expire
            else:
                self.delete_file('storage/cache' + key)
                n += 1
        with open(filename, 'wb') as output:
            pickle.dump(res, output, pickle.HIGHEST_PROTOCOL)

        Log().info(f'delete_expired success: {n} files')

    def delete_file(self,path, n=0):
        path = path.strip(' \n')
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            if n < 3:
                return self.delete_file(path, n + 1)
        return True

    def check_pass(self,line):
        res = line.split('<=>', 1)
        if len(res) < 2:
            return True
        expired, path = res
        if (datetime.strptime(expired, '%Y-%m-%d %H:%M:%S').timestamp() < datetime.utcnow().timestamp()):
            self.delete_file('storage/cache' + path)
            return False
        return True

    def add_to_list(self,path, expire, n=0):
        filename = 'storage/cache/r/en/usl/ist'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            with open(filename, 'rb') as input:
                data = pickle.load(input)
        except Exception:
            if n < 3:
                self.add_to_list(path, expire, n + 1)
                return
            data = {}
        data[path] = expire
        with open(filename, 'wb') as output:
            pickle.dump(data, output, pickle.HIGHEST_PROTOCOL)

    def create_if_not_exist(self,path, value, expire, n=0):
        filename = 'storage/cache' + path
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as output:
                pickle.dump(expire, output, pickle.HIGHEST_PROTOCOL)
                pickle.dump(value, output, pickle.HIGHEST_PROTOCOL)
        except:
            if n < 3:
                self.create_if_not_exist(path, value, expire, n + 1)

    def read_key(self,path, default=None, n=0):
        filename = 'storage/cache' + path
        if not os.path.exists(filename):
            return {'value': default, 'expire': -1}

        try:
            with open(filename, 'rb') as input:
                expire = pickle.load(input)
                value = pickle.load(input)
        except Exception:
            if n < 3:
                return self.read_key(path, default, n + 1)
            else:
                return {'value': default, 'expire': -1}

        if expire.timestamp() < datetime.utcnow().timestamp():
            self.delete_file(filename)
            return {'value': default, 'expire': -1}
        return {'value': value, 'expire': expire}

def cache_func(time: int, prefix=''):
    def dec(func):
        name = func.__name__
        file = func.__code__.co_filename

        def wrapper(*args, **kw):
            k = prefix + file + name
            for i in args:
                if type(i) in [str,int,float,list,dict,tuple,set]:
                    k = k + hash_key(i)

            has = Cache().get(k, 'no_cached')
            if has != 'no_cached':
                return has

            f = func(*args, **kw)
            Cache().put(k, f, time)
            return f

        return wrapper

    return dec

def build_name(key: str, depth):
    h_key = hash_key(key)
    res = ''
    d = 1
    s = 0
    e = 2
    while d < depth + 1:
        d += 1
        res += '/' + h_key[s:e]
        s = e
        e += 2
    res += '/' + h_key[s:]
    return res

