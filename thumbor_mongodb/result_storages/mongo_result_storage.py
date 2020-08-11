# -*- coding: utf-8 -*-
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 ekapratama93

import time
from datetime import datetime, timedelta
import pytz

import gridfs
from pymongo.errors import PyMongoError
from tornado.concurrent import return_future
from thumbor.engines import BaseEngine
from thumbor.result_storages import BaseStorage, ResultStorageResult
from thumbor.utils import logger
from thumbor_mongodb.utils import OnException
from thumbor_mongodb.mongodb.connector_result_storage import MongoConnector


class Storage(BaseStorage):

    '''start_time is used to calculate the last modified value when an item
    has no expiration date.
    '''
    start_time = None

    def __init__(self, context):
        BaseStorage.__init__(self, context)
        self.database, self.storage = self.__conn__()

        if not Storage.start_time:
            Storage.start_time = time.time()
        super(Storage, self).__init__(context)

    def __conn__(self):
        '''Return the MongoDB database and collection object.
        :returns: MongoDB DB and Collection
        :rtype: pymongo.database.Database, pymongo.database.Collection
        '''

        mongo_conn = MongoConnector(
            uri=self.context.config.MONGO_RESULT_STORAGE_URI,
            host=self.context.config.MONGO_RESULT_STORAGE_SERVER_HOST,
            port=self.context.config.MONGO_RESULT_STORAGE_SERVER_PORT,
            db_name=self.context.config.MONGO_RESULT_STORAGE_SERVER_DB,
            col_name=self.context.config.MONGO_RESULT_STORAGE_SERVER_COLLECTION
        )

        database = mongo_conn.db_conn
        storage = mongo_conn.col_conn

        return database, storage

    def on_mongodb_error(self, fname, exc_type, exc_value):
        '''Callback executed when there is a redis error.
        :param string fname: Function name that was being called.
        :param type exc_type: Exception type
        :param Exception exc_value: The current exception
        :returns: Default value or raise the current exception
        '''

        logger.error("[MONGODB_RESULT_STORAGE] %s,%s" % exc_type, exc_value)
        if fname == '_exists':
            return False
        return None

    def is_auto_webp(self):
        '''
        TODO This should be moved into the base storage class.
             It is shared with file_result_storage
        :return: If the file is a webp
        :rettype: boolean
        '''

        return self.context.config.AUTO_WEBP \
            and self.context.request.accepts_webp

    def get_key_from_request(self):
        '''Return a key for the current request url.
        :return: The storage key for the current url
        :rettype: string
        '''

        path = "result:%s" % self.context.request.url

        if self.is_auto_webp():
            path += '/webp'

        return path

    def get_max_age(self):
        '''Return the TTL of the current request.
        :returns: The TTL value for the current request.
        :rtype: int
        '''

        default_ttl = self.context.config.RESULT_STORAGE_EXPIRATION_SECONDS

        return default_ttl

    def is_expired(self, key):
        """
        Tells whether key has expired
        :param string key: Path to check
        :return: Whether it is expired or not
        :rtype: bool
        """
        if key:
            expire = self.get_max_age

            if expire is None or expire == 0:
                return False

            image = next(self.storage.find({
                'key': key,
                'created_at': {
                    '$gte': datetime.utcnow() - timedelta(
                        seconds=self.get_max_age()
                    )
                },
            }, {
                'created_at': True, '_id': False
            }).limit(1), None)

            if image:
                return False
            else:
                return True
        else:
            return True

    @OnException(on_mongodb_error, PyMongoError)
    def put(self, bytes):
        '''Save to mongodb
        :param bytes: Bytes to write to the storage.
        :return: MongoDB _id for the current url
        :rettype: string
        '''

        doc = {
            'key': self.get_key_from_request(),
            'created_at': datetime.utcnow()
        }

        if self.context.config.get("MONGO_STORE_METADATA", False):
            doc['metadata'] = dict(self.context.headers)
        else:
            doc['metadata'] = {}

        file_doc = dict(doc)

        file_storage = gridfs.GridFS(self.database)
        file_data = file_storage.put(bytes, **doc)

        file_doc['file_id'] = file_data
        self.storage.insert_one(file_doc)

    @return_future
    def get(self, callback):
        '''Get the item from MongoDB.'''

        key = self.get_key_from_request()
        callback(self._get(key))

    @OnException(on_mongodb_error, PyMongoError)
    def _get(self, key):
        stored = next(self.storage.find({
            'key': key,
            'created_at': {
                '$gte': datetime.utcnow() - timedelta(
                    seconds=self.get_max_age()
                )
            },
        }, {
            'file_id': True,
            'created_at': True,
            'metadata': True
        }).limit(1), None)

        if not stored:
            return None

        file_storage = gridfs.GridFS(self.database)

        contents = file_storage.get(stored['file_id']).read()

        metadata = stored['metadata']
        metadata['LastModified'] = stored['created_at'].replace(
            tzinfo=pytz.utc
        )
        metadata['ContentLength'] = len(contents)
        metadata['ContentType'] = BaseEngine.get_mimetype(contents)
        result = ResultStorageResult(
            buffer=contents,
            metadata=metadata,
            successful=True
        )
        return result

    @OnException(on_mongodb_error, PyMongoError)
    def last_updated(self):
        '''Return the last_updated time of the current request item
        :return: A DateTime object
        :rettype: datetetime.datetime
        '''

        key = self.get_key_from_request()
        max_age = self.get_max_age()

        if max_age == 0:
            return datetime.fromtimestamp(Storage.start_time)

        image = next(self.storage.find({
            'key': key,
            'created_at': {
                '$gte': datetime.utcnow() - timedelta(
                    seconds=self.get_max_age()
                )
            },
        }, {
            'created_at': True, '_id': False
        }).limit(1), None)

        if image:
            age = int(
                (datetime.utcnow() - image['created_at']).total_seconds()
            )
            ttl = max_age - age

            if max_age <= 0:
                return datetime.fromtimestamp(Storage.start_time)

            if ttl >= 0:
                return datetime.utcnow() - timedelta(
                    seconds=(
                        max_age - ttl
                    )
                )

        # Should never reach here. It means the storage put failed or the item
        # somehow does not exists anymore
        return datetime.utcnow()
