# -*- coding: utf-8 -*-
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 ekapratama93

from pymongo import ASCENDING, DESCENDING, MongoClient


class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super(Singleton, cls).__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class MongoConnector(object):
    __metaclass__ = Singleton

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
        self.ensure_index()

    def create_connection(self):
        if self.uri:
            connection = MongoClient(self.uri)
        else:
            connection = MongoClient(self.host, self.port)

        db_conn = connection[self.db_name]
        col_conn = db_conn[self.col_name]

        return db_conn, col_conn

    def ensure_index(self):
        index_name = 'key_1_created_at_-1'
        if index_name not in self.col_conn.index_information():
            self.col_conn.create_index(
                [('key', ASCENDING), ('created_at', DESCENDING)],
                name=index_name
            )
