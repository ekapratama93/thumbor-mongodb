#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 Eka Cahya Pratama <ekapratama93@gmail.com>

import time
from datetime import datetime

import mock
from preggy import expect
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase, gen_test

from tests.fixtures.fixtures import IMAGE_BYTES
from thumbor.app import ThumborServiceApp
from thumbor.config import Config
from thumbor.context import RequestParameters, Context
from thumbor.importer import Importer
from thumbor.result_storages import ResultStorageResult
from thumbor_mongodb.result_storages.mongo_result_storage import Storage


class BaseMongoResultStorageTestCase(AsyncHTTPTestCase):
    def get_app(self):
        self.context = self.get_context()
        return ThumborServiceApp(self.context)

    def get_server(self):  # pylint: disable=no-self-use
        return None

    def get_importer(self):
        importer = Importer(self.config)
        importer.import_modules()
        return importer

    def get_request_handler(self):  # pylint: disable=no-self-use
        return None

    def get_context(self):
        self.config = (  # pylint: disable=attribute-defined-outside-init
            self.get_config()
        )
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=assignment-from-none
        self.server = (
            self.get_server()
        )
        self.importer = (  # pylint: disable=attribute-defined-outside-init
            self.get_importer()
        )
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=assignment-from-none
        self.request_handler = (
            self.get_request_handler()
        )
        self.importer.import_modules()
        return Context(
            self.server, self.config, self.importer, self.request_handler
        )

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self, *args, **kw):
        super(BaseMongoResultStorageTestCase, self).setUp(*args, **kw)

        self.context = None
        self.storage = None

        self.context = mock.Mock(
            config=self.get_config(),
            request=self.get_request(),
        )
        self.storage = Storage(self.context)

    def get_config(self):
        return Config(
            MONGO_RESULT_STORAGE_URI='mongodb://localhost:27017',
            MONGO_RESULT_STORAGE_SERVER_DB='thumbor',
            MONGO_RESULT_STORAGE_SERVER_COLLECTION='images',
            MONGODB_RESULT_STORAGE_IGNORE_ERRORS=False,
        )

    @staticmethod
    def get_request():
        return RequestParameters()

    @gen_test
    async def test_get_key_from_request(self):
        expect(self.storage).not_to_be_null()
        expect(self.storage.get_key_from_request()).to_equal(
            f"result:{self.storage.context.request.url}"
        )

    @gen_test
    async def test_auto_webp_path(self):
        config = self.get_config()
        config.AUTO_WEBP = True
        ctx = mock.Mock(
            config=config,
            request=RequestParameters(accepts_webp=True)
        )
        storage = Storage(ctx)

        expect(storage).not_to_be_null()
        expect(storage.get_key_from_request()).to_equal(
            f"result:{storage.context.request.url}/webp"
        )

    @gen_test
    async def test_can_get_image_from_storage(self):
        config = self.get_config()
        config.RESULT_STORAGE_EXPIRATION_SECONDS = 5
        ctx = mock.Mock(
            config=config,
            request=mock.Mock(
                url="image.jpg"
            )
        )
        storage = Storage(ctx)

        insert = await storage.put(IMAGE_BYTES)
        expect(insert).to_equal("image.jpg")
        expect(insert).Not.to_be_an_error()

        result = await storage.get()
        expect(result).to_be_instance_of(ResultStorageResult)
        expect(result.successful).to_equal(True)
        expect(len(result)).to_equal(7339)
        expect(len(result)).to_equal(result.metadata["ContentLength"])
        expect(result.last_modified).to_be_instance_of(datetime)

    @gen_test
    async def test_can_get_image_using_old_config(self):
        config = Config(
            MONGO_RESULT_STORAGE_SERVER_HOST="localhost",
            MONGO_RESULT_STORAGE_SERVER_PORT=27017,
            MONGO_RESULT_STORAGE_SERVER_DB='thumbor',
            MONGO_RESULT_STORAGE_SERVER_COLLECTION='images',
        )
        config.RESULT_STORAGE_EXPIRATION_SECONDS = 5
        ctx = mock.Mock(
            config=config,
            request=mock.Mock(
                url="image_old_config.jpg"
            )
        )
        storage = Storage(ctx)

        insert = await storage.put(IMAGE_BYTES)
        expect(insert).to_equal("image_old_config.jpg")
        expect(insert).Not.to_be_an_error()

        result = await storage.get()
        expect(result).to_be_instance_of(ResultStorageResult)
        expect(result.successful).to_equal(True)
        expect(len(result)).to_equal(7339)
        expect(len(result)).to_equal(result.metadata["ContentLength"])
        expect(result.last_modified).to_be_instance_of(datetime)

    @gen_test
    async def test_can_last_updated(self):
        config = self.get_config()
        ctx = mock.Mock(
            config=config,
            request=mock.Mock(
                url="image.jpg"
            )
        )
        storage = Storage(ctx)

        result = storage.last_updated()
        expect(result).to_be_instance_of(datetime)
        expect(result).Not.to_be_an_error()

    @gen_test
    async def test_cannot_get_expired_image(self):
        config = self.get_config()
        config.RESULT_STORAGE_EXPIRATION_SECONDS = 5
        ctx = mock.Mock(
            config=config,
            request=mock.Mock(
                url="image.jpg"
            )
        )
        storage = Storage(ctx)
        time.sleep(ctx.config.RESULT_STORAGE_EXPIRATION_SECONDS)
        result = await storage.get()
        expect(result).to_be_null()

    @gen_test
    async def test_can_store_image_with_metadata(self):
        config = self.get_config()
        config.RESULT_STORAGE_EXPIRATION_SECONDS = 5
        config.MONGO_STORE_METADATA = True

        ctx = self.get_context()
        ctx.config = config
        ctx.request = RequestParameters(url="image_2.jpg")

        storage = Storage(ctx)

        insert = await storage.put(IMAGE_BYTES)
        expect(insert).to_equal("image_2.jpg")
        expect(insert).Not.to_be_an_error()

