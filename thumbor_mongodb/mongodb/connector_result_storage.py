# -*- coding: utf-8 -*-
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 Eka Cahya Pratama <ekapratama93@gmail.com>

from motor.motor_tornado import MotorClient
from pymongo import ASCENDING, DESCENDING
from tornado.gen import convert_yielded


class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class MongoConnector(metaclass=Singleton):

    def __init__(self,
                 uri=None,
                 host=None,
                 port=None,
                 db_name=None,
                 col_name=None):
        self.uri = uri
        self.host = host
        self.port = port
        self.db_name = db_name
        self.col_name = col_name
        self.db_conn, self.col_conn = self.create_connection()
        convert_yielded(self.ensure_index())

    def create_connection(self):
        if self.uri:
            connection = MotorClient(self.uri)
        else:
            connection = MotorClient(self.host, self.port)

        db_conn = connection[self.db_name]
        col_conn = db_conn[self.col_name]

        return db_conn, col_conn

    async def ensure_index(self):
        index_name = 'key_1_created_at_-1'
        indexes = await self.col_conn.index_information()
        if index_name not in indexes:
            await self.col_conn.create_index(
                [('key', ASCENDING), ('created_at', DESCENDING)],
                name=index_name
            )
