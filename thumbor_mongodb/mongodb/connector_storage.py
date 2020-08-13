# -*- coding: utf-8 -*-
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 ekapratama93

from motor.motor_tornado import MotorClient
from pymongo import ASCENDING, DESCENDING


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
        self.ensure_index().next()

    def create_connection(self):
        if self.uri:
            connection = MotorClient(self.uri)
        else:
            connection = MotorClient(self.host, self.port)

        db_conn = connection[self.db_name]
        col_conn = db_conn[self.col_name]

        return db_conn, col_conn

    def get_index_information(self):
        yield self.col_conn.index_information()
        return

    def ensure_index(self):
        index_name = 'path_1_created_at_-1'
        indexes = self.get_index_information()
        if index_name not in indexes:
            yield self.col_conn.create_index(
                [('path', ASCENDING), ('created_at', DESCENDING)],
                name=index_name
            )
