import os
import typing
from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime

from renus.core.config import Config
from renus.core.request import Request


class ModelBase:
    metro = None

    def __init__(self, collection_name: str, request: Request) -> None:
        self._request = request
        self._config = Config('database', request)
        self._collection_name = collection_name
        self._database_name = self._config.get('name', 'renus')
        self._client = MongoClient(self._config.get('host', '127.0.0.1'),
                                   self._config.get('port', '27017'),
                                   username=self._config.get('username', None),
                                   password=self._config.get('password', None))

        self.hidden_fields = [
            'password'
        ]
        self.cast_fields = [
            '_id', 'created_at', 'updated_at'
        ]
        self._steps = None
        self._where = None
        self._distinct = None
        self._limit = None
        self._skip = None
        self._sort = None
        self._select = None

    def set_database(self, name: str):
        self._database_name = name

    def set_collection(self, name: str):
        self._collection_name = name

    @property
    def db(self):
        return self._client[self._database_name]

    def collection(self, name: str = None):
        if name is None:
            name = self._collection_name
        return self.db[name]

    def create_index(self, fields, unique=False):
        return self.collection().create_index(fields,
                                              unique=unique)

    def aggregate(self, pipeline: typing.Any, session: typing.Any = None):
        return self.__police(self.collection().aggregate(pipeline, session))

    def where(self, where: dict):
        self._where = where
        if self._steps is not None:
            self._steps.append({
                "$match": where
            })
        return self

    def count(self, skip=False, limit=False):
        k = {}
        if self._where is not None:
            k['filter'] = self._where
        else:
            k['filter'] = {}
        if skip and self._skip is not None:
            k['skip'] = self._skip
        if limit and self._limit is not None:
            k['limit'] = self._limit
        return self.collection().count_documents(**k)

    def distinct(self, key: str):
        self._distinct = key
        return self

    def limit(self, count: int):
        self._limit = count
        if self._steps is not None:
            self._steps.append({"$limit": self._limit})
        return self

    def skip(self, count: int):
        self._skip = count
        if self._steps is not None:
            self._steps.append({"$skip": self._skip})
        return self

    def group(self, item:dict):
        if self._steps is None:
            raise RuntimeError("group work with steps() architect")
        self._steps.append({"$group": item})
        return self

    def sort(self, key_or_list: typing.Union[str, typing.List[typing.Tuple]], asc: bool = True):
        if type(key_or_list) is dict:
            self._sort=key_or_list
        elif type(key_or_list) is list:
            self._sort = []
            for f, a in key_or_list:
                self._sort.append((f,1 if a else -1))
        else:
            self._sort = [(key_or_list,1 if asc else -1)]
        if self._steps is not None:
            if type(self._sort) is list:
                self._sort={i[0]:i[1] for i in self._sort}

            self._steps.append({"$sort": self._sort})
        return self

    def select(self, *select: [str,typing.Dict]):
        if self._steps is not None:
            self._steps.append({'$project': select[0]})
            return self
        self._select = {}
        for key in select:
            if type(key) is dict:
                self._select = key
            else:
                self._select[key]=1
        return self

    def __cleaner(self, document: dict):
        for field in self.hidden_fields:
            if field in document:
                del document[field]
        for field in self.cast_fields:
            if field in document:
                if type(document[field]) is dict:
                    document[field] = self.__cleaner(document[field])
                elif type(document[field]) is list:
                    res = []
                    for doc in document[field]:
                        if type(doc) is dict:
                            res.append(self.__cleaner(doc))
                        else:
                            res.append(str(doc))
                    document[field] = res
                else:
                    document[field] = str(document[field])
        return document

    def __police(self, documents: typing.Any):
        if documents is None:
            return None
        res = []
        if type(documents) is dict:
            return self.__cleaner(documents)
        else:
            for document in documents:
                if type(document) is dict:
                    res.append(self.__cleaner(document))
        return res

    def with_relation(self, collection, local_field, forigen_field, to=None):
        if self._steps is not None:
            self._steps.append({
                    "$lookup": {
                        "from": collection,
                        "localField": local_field,
                        "foreignField": forigen_field,
                        "as": to or collection
                    }
                })
        return self

    def steps(self):
        self._steps=[]
        return self

    def get(self, police: bool = True) -> list:
        if self._steps is not None:
            return self.aggregate(self._steps)

        where, select = self._base_gate(police)

        find = self.collection().find(where, select)

        if self._sort is not None:
            find = find.sort(self._sort)
        if self._skip is not None:
            find = find.skip(self._skip)
        if self._limit is not None:
            find = find.limit(self._limit)
        if self._distinct is not None:
            return find.distinct(self._distinct)

        return self.__police(find) if police else list(find)

    def first(self, police: bool = True) -> typing.Union[None, dict]:
        self._limit = 1
        res = self.get(police)
        self._limit = None
        if len(res) == 1:
            return res[0]
        return None

    def _base_gate(self, police) -> list:
        where = self._where
        select = self._select

        if select is None and police == False:
            raise RuntimeError("when police is off, for security reason select fields. ex: .select('_id','name')")

        if where is not None:
            if '_id' in where:
                where['_id'] = self.convert_id(where['_id'])

        return [where, select]

    def create(self, document: dict) -> ObjectId:
        if "updated_at" not in document:
            document["updated_at"] = datetime.utcnow()

        if "created_at" not in document:
            document["created_at"] = datetime.utcnow()

        id = self.collection().insert_one(document).inserted_id
        document['_id'] = id
        self.boot_event('create', {}, document)
        return id

    def create_many(self, documents: typing.List) -> typing.List[ObjectId]:
        for document in documents:
            if "updated_at" not in document:
                document["updated_at"] = datetime.utcnow()

            if "created_at" not in document:
                document["created_at"] = datetime.utcnow()

        ids = self.collection().insert_many(documents).inserted_ids
        self.boot_event('create_many', {}, ids)
        return ids

    def update(self, new: dict, upsert=False) -> bool:
        where = self.__ud_gate('update')
        new["updated_at"] = datetime.utcnow()
        old = self.collection().find_one_and_update(where,
                                                    {"$set": new, '$setOnInsert': {'created_at': datetime.utcnow()}},
                                                    upsert=upsert)
        self.boot_event('update', old, new)
        return True

    def update_opt(self, new: dict, upsert=False) -> bool:
        where = self.__ud_gate('update')
        if '$set' not in new:
            new['$set'] = {}
        if '$setOnInsert' not in new:
            new['$setOnInsert'] = {}
        new['$set']["updated_at"] = datetime.utcnow()
        new['$setOnInsert']['created_at'] = datetime.utcnow()
        old = self.collection().update(where, new, upsert=upsert)
        self.boot_event('update', old, new)
        return True

    def update_many(self, new: dict) -> bool:
        where = self.__ud_gate('update')
        new["updated_at"] = datetime.utcnow()
        old = self.collection().update_many(where, {"$set": new}).raw_result
        self.boot_event('update_many', old, new)
        return True

    def delete(self, all: bool = False) -> bool:
        where = self.__ud_gate('delete')
        if all is False:
            old = self.collection().find_one_and_delete(where)
            if self.metro is not None:
                self._handle_metro('delete', old)
            self.boot_event('delete', old, {})
        else:
            if self.metro is not None:
                self._handle_metro('delete')
            old = self.collection().delete_many(where)

            self.boot_event('delete_many', {'deleted_count': old.deleted_count, 'where': where}, {})

        return True

    def __ud_gate(self, type: str):
        where = self._where
        if where is None:
            raise RuntimeError(f"for {type} use where. ex: .where({'name':'test'})")
        if '_id' in where:
            where['_id'] = self.convert_id(where['_id'])

        return where

    def make_visible(self, fields: typing.List):
        for field in fields:
            if field in self.hidden_fields:
                self.hidden_fields.remove(field)
        return self

    def boot_event(self, typ: str, old, new):
        pass

    def convert_id(self, id):
        if type(id) is str:
            try:
                return ObjectId(id)
            except Exception:
                return id
        return id

    def _handle_metro(self, typ, obj=None):
        if typ == 'delete':
            if obj is None:
                where = self.__ud_gate('delete')
                all = self.collection().find(where)
            else:
                all = [obj]

            for item in all:
                for field, db in self.metro.items():
                    if type(db) is dict:
                        for c, f in db.items():
                            f = f.split(':')
                            i = item[field]
                            if len(f) > 1:
                                if f[1] == 'str':
                                    i = str(i)
                                elif f[1] == 'int':
                                    i = int(i)
                                elif f[1] == 'bool':
                                    i = bool(i)
                            self.collection(c).delete_many({
                                f[0]: i
                            })

                    else:
                        if field in item:
                            self._remove_file(item[field])

    def _remove_file(self, links):
        if type(links) is not list:
            links = [links]

        for link in links:
            link = link.replace('storage/img/', '', 1)
            link = link.replace('storage/', '', 1)
            try:
                os.remove(f'storage/{Config("app", self._request).get("public_folder", "public")}/' + link)
            except:
                pass
