# -*- coding: utf-8 -*-
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 Eka Cahya Pratama <ekapratama93@gmail.com>

from datetime import datetime, timedelta
from motor.motor_tornado import MotorGridFSBucket
from pymongo.errors import PyMongoError
from thumbor.engines import BaseEngine
from thumbor.result_storages import BaseStorage, ResultStorageResult
from thumbor.utils import deprecated, logger
from thumbor_mongodb.mongodb.connector_result_storage import MongoConnector
from thumbor_mongodb.utils import OnException
import pytz


class Storage(BaseStorage):

    def __init__(self, context):
        BaseStorage.__init__(self, context)
        self.database, self.storage = self.__conn__()
        super(Storage, self).__init__(context)

    def __conn__(self):
        '''Return the MongoDB database and collection object.
        :returns: MongoDB DB and Collection
        :rtype: pymongo.database.Database, pymongo.database.Collection
        '''

        db_name = self.context.config.MONGO_RESULT_STORAGE_SERVER_DB
        col_name = self.context.config.MONGO_RESULT_STORAGE_SERVER_COLLECTION
        uri = None
        host = None
        port = None
        try:
            uri = self.context.config.MONGO_RESULT_STORAGE_URI
        except AttributeError:
            pass

        try:
            host = self.context.config.MONGO_RESULT_STORAGE_SERVER_HOST
            port = self.context.config.MONGO_RESULT_STORAGE_SERVER_PORT
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

        if self.context.config.MONGODB_RESULT_STORAGE_IGNORE_ERRORS:
            logger.error(f"[MONGODB_RESULT_STORAGE] {exc_type}, {exc_value}")
            if fname == '_exists':
                return False
            return None
        else:
            raise exc_value

    @property
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

        path = f"result:{self.context.request.url}"

        if self.is_auto_webp:
            return f'{path}/webp'

        return path

    def get_max_age(self):
        '''Return the TTL of the current request.
        :returns: The TTL value for the current request.
        :rtype: int
        '''

        default_ttl = self.context.config.RESULT_STORAGE_EXPIRATION_SECONDS

        return default_ttl

    @OnException(on_mongodb_error, PyMongoError)
    async def put(self, image_bytes):
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

        fs = MotorGridFSBucket(self.database)
        file_id = await fs.upload_from_stream(
            filename=file_doc.get('key'),
            source=image_bytes,
            metadata=file_doc
        )

        file_doc['file_id'] = file_id
        file_doc['content_type'] = BaseEngine.get_mimetype(image_bytes)
        file_doc['content_length'] = len(image_bytes)

        await self.storage.insert_one(file_doc)
        return self.context.request.url

    @OnException(on_mongodb_error, PyMongoError)
    async def get(self):
        '''Get the item from MongoDB.'''

        key = self.get_key_from_request()
        age = datetime.utcnow() - timedelta(
            seconds=self.get_max_age()
        )
        stored = await self.storage.find_one({
            'key': key,
            'created_at': {
                '$gte': age
            },
        }, {
            'file_id': True,
            'created_at': True,
            'metadata': True,
            'content_type': True,
            'content_length': True,
        })

        if not stored:
            return None

        fs = MotorGridFSBucket(self.database)
        grid_out = await fs.open_download_stream(stored['file_id'])
        contents = await grid_out.read()

        metadata = stored['metadata']
        metadata['LastModified'] = stored['created_at'].replace(
            tzinfo=pytz.utc
        )
        metadata['ContentLength'] = stored['content_length']
        metadata['ContentType'] = stored['content_type']
        return ResultStorageResult(
            buffer=contents,
            metadata=metadata,
            successful=True
        )

    @deprecated("Use result's last_modified instead")
    def last_updated(self):
        '''Return the last_updated time of the current request item
        :return: A DateTime object
        :rettype: datetetime.datetime
        '''

        # TODO: add actual code to check last_updated using async motor
        # in non async function.
        return datetime.utcnow()
