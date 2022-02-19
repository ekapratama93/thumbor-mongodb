# -*- coding: utf-8 -*-
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 Eka Cahya Pratama <ekapratama93@gmail.com>
# Copyright (c) 2015 Thumbor-Community
# Copyright (c) 2011 globo.com timehome@corp.globo.com

from datetime import datetime, timedelta
from motor.motor_tornado import MotorGridFSBucket
from pymongo.errors import PyMongoError
from thumbor.storages import BaseStorage
from thumbor.utils import logger
from thumbor_mongodb.utils import OnException
from thumbor_mongodb.mongodb.connector_storage import MongoConnector


class Storage(BaseStorage):

    def __init__(self, context):
        '''Initialize the MongoStorage

        :param thumbor.context.Context shared_client: Current context
        '''
        BaseStorage.__init__(self, context)
        self.database, self.storage = self.__conn__()
        super(Storage, self).__init__(context)

    def __conn__(self):
        '''Return the MongoDB database and collection object.
        :returns: MongoDB DB and Collection
        :rtype: pymongo.database.Database, pymongo.database.Collection
        '''

        db_name = self.context.config.MONGO_STORAGE_SERVER_DB
        col_name = self.context.config.MONGO_STORAGE_SERVER_COLLECTION
        uri = None
        host = None
        port = None
        try:
            uri = self.context.config.MONGO_STORAGE_URI
        except AttributeError:
            pass

        try:
            host = self.context.config.MONGO_STORAGE_SERVER_HOST
            port = self.context.config.MONGO_STORAGE_SERVER_PORT
        except AttributeError:
            pass

        mongo_conn = MongoConnector(
            db_name=db_name,
            col_name=col_name,
            uri=uri,
            host=host,
            port=port,
        )

        database = mongo_conn.db_conn
        storage = mongo_conn.col_conn

        return database, storage

    def on_mongodb_error(self, fname, exc_type, exc_value):
        '''Callback executed when there is a mongo error.
        :param string fname: Function name that was being called.
        :param type exc_type: Exception type
        :param Exception exc_value: The current exception
        :returns: Default value or raise the current exception
        '''

        if not self.context.config.MONGODB_STORAGE_IGNORE_ERRORS:
            raise exc_value
        logger.error(f"[MONGODB_STORAGE] {exc_type}, {exc_value}")
        if fname == 'exists':
            return False
        return None

    def get_max_age(self):
        '''Return the TTL of the current request.
        :returns: The TTL value for the current request.
        :rtype: int
        '''

        return self.context.config.STORAGE_EXPIRATION_SECONDS

    @OnException(on_mongodb_error, PyMongoError)
    async def put(self, path, file_bytes):
        doc = {
            'path': path,
            'created_at': datetime.utcnow()
        }

        doc_with_crypto = dict(doc)
        if self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
            if not self.context.server.security_key \
               or self.context.server.security_key == "":
                raise RuntimeError(
                    "STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True \
                        if no SECURITY_KEY specified")
            doc_with_crypto['crypto'] = self.context.server.security_key

        fs = MotorGridFSBucket(self.database)
        file_id = await fs.upload_from_stream(
            filename=doc.get('path'),
            source=file_bytes,
            metadata=doc
        )
        doc_with_crypto['file_id'] = file_id
        await self.storage.insert_one(doc_with_crypto)
        return path

    @OnException(on_mongodb_error, PyMongoError)
    async def put_crypto(self, path):
        if not self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
            return None

        if not self.context.server.security_key:
            raise RuntimeError("STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be \
                True if no SECURITY_KEY specified")

        await self.storage.update_one(
            {'path': path},
            {'$set': {'crypto': self.context.server.security_key}}
        )
        return path

    @OnException(on_mongodb_error, PyMongoError)
    async def put_detector_data(self, path, data):
        await self.storage.update_many(
            {'path': path}, {"$set": {"detector_data": data}}
        )
        return path

    @OnException(on_mongodb_error, PyMongoError)
    async def get_crypto(self, path):
        crypto = await self.storage.find_one({'path': path})
        return crypto.get('crypto') if crypto else None

    @OnException(on_mongodb_error, PyMongoError)
    async def get_detector_data(self, path):
        doc = await self.storage.find_one({
            'path': path,
            'detector_data': {'$ne': None},
        }, {
            'detector_data': True,
        })

        return doc.get('detector_data') if doc else None

    @OnException(on_mongodb_error, PyMongoError)
    async def get(self, path):
        now = datetime.utcnow()
        query = {'path': path}
        if self.get_max_age():
            query['created_at'] = {
                '$gte': now - timedelta(seconds=self.get_max_age())
            }
        stored = await self.storage.find_one(query, {'file_id': True})

        if not stored:
            return None

        fs = MotorGridFSBucket(self.database)
        grid_out = await fs.open_download_stream(stored['file_id'])
        return await grid_out.read()

    @OnException(on_mongodb_error, PyMongoError)
    async def exists(self, path):
        return await self.storage.count_documents({
            'path': path,
            'created_at': {
                '$gte':
                    datetime.utcnow() - timedelta(seconds=self.get_max_age())
            },
        }, limit=1) >= 1

    @OnException(on_mongodb_error, PyMongoError)
    async def remove(self, path):
        await self.storage.delete_many({'path': path})

        fs = MotorGridFSBucket(self.database)
        cursor = await fs.find({'path': path})
        while await cursor.fetch_next:
            grid_data = cursor.next_object()
            await fs.delete(grid_data["_id"])
