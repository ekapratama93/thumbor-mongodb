# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/globocom/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 ekapratama93

from datetime import datetime, timedelta
from thumbor_mongodb.result_storages.mongo_result_storage import Storage as MongoStorage
from pyvows import Vows, expect
from vows.fixtures.storage_fixtures import IMAGE_BYTES
import mock
import time


class MongoDBContext(Vows.Context):
    def setup(self):
        self.connection = MongoClient(
            'localhost',
            27017
        )
        self.database = self.connection['thumbor']
        self.storage = self.database['result_images']


@Vows.batch
class MongoResultStorage(MongoDBContext):
    class CanStoreImage(Vows.Context):
        def topic(self):
            self.url = 'https://wikipedia.org'
            self.context = mock.Mock(
                config=mock.Mock(
                    MONGO_RESULT_STORAGE_URI="",
                    MONGO_RESULT_STORAGE_SERVER_HOST='localhost',
                    MONGO_RESULT_STORAGE_SERVER_PORT=27017,
                    MONGO_RESULT_STORAGE_SERVER_DB='thumbor',
                    MONGO_RESULT_STORAGE_SERVER_COLLECTION='images',
                    MAX_AGE=10,
                    AUTO_WEBP=False,
                    RESULT_STORAGE_EXPIRATION_SECONDS=10,
                ),
                request=mock.Mock(
                    url=self.url
                ),
                headers={"Accept":""}
            )
            return MongoStorage(self.context)

        def can_create_storage(self, topic):
            expect(topic).not_to_be_null()

        def can_store_to_storage(self, topic):
            topic.put(IMAGE_BYTES)
            expect(topic).Not.to_be_an_error()
            expected = ('result:%s' % self.url)
            expect(topic.get_key_from_request()).to_equal(expected)
            result = topic.get().result()
            expect(result.buffer).to_equal(IMAGE_BYTES)

        def can_get_last_update(self, topic):
            expect(topic.last_updated()).to_be_lesser_than(
                datetime.utcnow() + timedelta(seconds=self.context.config.MAX_AGE)
            )

        def can_get_is_expired(self, topic):
            key = topic.get_key_from_request()
            expect(topic.is_expired(key)).to_be_false()
            time.sleep(self.context.config.MAX_AGE)
            expect(topic.is_expired(key)).to_be_true()

        class KnowsImageDoesNotExist(Vows.Context):
            def topic(self):
                url = 'https://wikipedia.org/image'
                self.context = mock.Mock(
                    config=mock.Mock(
                        MONGO_RESULT_STORAGE_URI="",
                        MONGO_RESULT_STORAGE_SERVER_HOST='localhost',
                        MONGO_RESULT_STORAGE_SERVER_PORT=27017,
                        MONGO_RESULT_STORAGE_SERVER_DB='thumbor',
                        MONGO_RESULT_STORAGE_SERVER_COLLECTION='images',
                        AUTO_WEBP=True,
                        MAX_AGE=10,
                        RESULT_STORAGE_EXPIRATION_SECONDS=10,
                    ),
                    request=mock.Mock(
                        url=url
                    ),
                    headers={"Accept":""}
                )
                return MongoStorage(self.context)

            def should_not_exist(self, topic):
                result = topic.get()
                expect(result.exception()).not_to_be_an_error()
                expect(result.result()).not_to_be_null()

        class StoreImageWithAutoWebp(Vows.Context):
            def topic(self):
                self.url = 'https://wikipedia.org/image'
                self.context = mock.Mock(
                    config=mock.Mock(
                        MONGO_RESULT_STORAGE_URI="",
                        MONGO_RESULT_STORAGE_SERVER_HOST='localhost',
                        MONGO_RESULT_STORAGE_SERVER_PORT=27017,
                        MONGO_RESULT_STORAGE_SERVER_DB='thumbor',
                        MONGO_RESULT_STORAGE_SERVER_COLLECTION='images',
                        AUTO_WEBP=True,
                        MAX_AGE=10,
                        RESULT_STORAGE_EXPIRATION_SECONDS=10,
                    ),
                    request=mock.Mock(
                        url=self.url
                    ),
                    headers={"Accept":""}
                )
                return MongoStorage(self.context)

            def can_store_autowebp(self, topic):
                expect(topic.put(IMAGE_BYTES)).Not.to_be_an_error()
                expected = ('result:%s/webp' % self.url)
                expect(topic.get_key_from_request()).to_equal(expected)
                expect(topic.get().result().buffer).to_equal(IMAGE_BYTES)

