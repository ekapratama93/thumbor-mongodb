#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 Eka Cahya Pratama <ekapratama93@gmail.com>

import time

from preggy import expect
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase, gen_test

from tests.fixtures.fixtures import IMAGE_BYTES
from thumbor.app import ThumborServiceApp
from thumbor.config import Config
from thumbor.context import Context, ServerParameters
from thumbor.importer import Importer
from thumbor_mongodb.storages.mongo_storage import Storage as MongoStorage


class BaseMongoStorageTestCase(AsyncHTTPTestCase):
    def get_app(self):
        self.context = self.get_context()
        return ThumborServiceApp(self.context)

    def get_server(self):  # pylint: disable=no-self-use
        server = ServerParameters(
            8888, "localhost", "thumbor.conf", None, "info", None
        )
        server.security_key = "ACME-SEC"
        return server

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
        # pylint: assignment-from-none
        self.server = (
            self.get_server()
        )
        self.importer = (  # pylint: disable=attribute-defined-outside-init
            self.get_importer()
        )
        # pylint: disable=attribute-defined-outside-init
        # pylint: assignment-from-none
        self.request_handler = (
            self.get_request_handler()
        )
        self.importer.import_modules()
        return Context(
            self.server, self.config, self.importer, self.request_handler
        )

    def get_new_ioloop(self):
        return IOLoop.instance()

    def get_image_url(self, name):
        return "s.glbimg.com/some/{0}".format(name)

    def setUp(self, *args, **kw):
        super(BaseMongoStorageTestCase, self).setUp(*args, **kw)

        self.storage = MongoStorage(Context(
            config=self.get_config(), server=self.get_server()
        ))

    def get_config(self):
        return Config(
            MONGO_STORAGE_URI='mongodb://localhost:27017',
            MONGO_STORAGE_SERVER_DB='thumbor',
            MONGO_STORAGE_SERVER_COLLECTION='images',
            MONGODB_STORAGE_IGNORE_ERRORS=False,
        )

    @gen_test
    async def test_can_store_image_should_be_in_catalog(self):
        url = self.get_image_url("image.png")
        await self.storage.put(url, IMAGE_BYTES)
        result = await self.storage.get(url)
        expect(result).not_to_be_null()
        expect(result).not_to_be_an_error()

    @gen_test
    async def test_can_store_image_with_spaces(self):
        url = self.get_image_url("image .jpg")
        await self.storage.put(url, IMAGE_BYTES)
        result = await self.storage.get(url)
        expect(result).not_to_be_null()
        expect(result).not_to_be_an_error()
        expect(result).to_equal(IMAGE_BYTES)

    @gen_test
    async def test_can_store_image_with_spaces_encoded(self):
        url = self.get_image_url("image%20.jpg")
        await self.storage.put(url, IMAGE_BYTES)
        got = await self.storage.get(url)
        expect(got).not_to_be_null()
        expect(got).not_to_be_an_error()
        expect(got).to_equal(IMAGE_BYTES)

    @gen_test
    async def test_can_get_image(self):
        iurl = self.get_image_url("image_2.jpg")
        await self.storage.put(iurl, IMAGE_BYTES)
        got = await self.storage.get(iurl)
        expect(got).not_to_be_null()
        expect(got).not_to_be_an_error()
        expect(got).to_equal(IMAGE_BYTES)

    @gen_test
    async def test_does_not_store_if_config_says_not_to(self):
        iurl = self.get_image_url("image_5.jpg")
        await self.storage.put(iurl, IMAGE_BYTES)
        await self.storage.put_crypto(iurl)
        got = await self.storage.get_crypto(iurl)
        expect(got).to_be_null()

    @gen_test
    async def test_detector_can_store_detector_data(self):
        iurl = self.get_image_url("image_7.jpg")
        await self.storage.put(iurl, IMAGE_BYTES)
        await self.storage.put_detector_data(iurl, "some-data")
        got = await self.storage.get_detector_data(iurl)
        expect(got).not_to_be_null()
        expect(got).not_to_be_an_error()
        expect(got).to_equal("some-data")

    @gen_test
    async def test_detector_returns_none_if_no_detector_data(self):
        iurl = self.get_image_url("image_10000.jpg")
        got = await self.storage.get_detector_data(iurl)
        expect(got).to_be_null()

    @gen_test
    async def test_cannot_get_expired_image(self):
        iurl = self.get_image_url("image_2.jpg")
        config = self.get_config()
        config.STORAGE_EXPIRATION_SECONDS = 5
        storage = MongoStorage(Context(
            config=config, server=self.get_server()
        ))
        await storage.put(iurl, IMAGE_BYTES)
        time.sleep(5)
        got = await storage.get(iurl)
        expect(got).to_be_null()
        expect(got).not_to_be_an_error()

    @gen_test
    async def test_can_get_if_expire_set_to_none(self):
        iurl = self.get_image_url("image_2.jpg")
        config = self.get_config()
        config.STORAGE_EXPIRATION_SECONDS = None
        storage = MongoStorage(Context(
            config=config, server=self.get_server()
        ))
        await storage.put(iurl, IMAGE_BYTES)
        got = await storage.get(iurl)
        expect(got).not_to_be_null()
        expect(got).not_to_be_an_error()

    @gen_test
    async def test_should_be_an_error(self):
        iurl = self.get_image_url("image_3.jpg")
        server = self.get_server()
        server.security_key = ""
        storage = MongoStorage(Context(
            config=self.get_config(), server=server
        ))
        await storage.put(iurl, IMAGE_BYTES)

        msg = ("STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True \
            if no SECURITY_KEY specified")

        await storage.put_crypto(iurl)
        expect.error_to_happen(RuntimeError, message=msg)

    @gen_test
    async def test_getting_crypto_for_a_new_image_returns_none(self):
        iurl = self.get_image_url("image_9999.jpg")
        config = self.get_config()
        config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE = True
        storage = MongoStorage(Context(
            config=config, server=self.get_server()
        ))
        got = await storage.get_crypto(iurl)
        expect(got).to_be_null()

    @gen_test
    async def test_can_store_crypto(self):
        iurl = self.get_image_url("image_6.jpg")
        config = self.get_config()
        config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE = True
        storage = MongoStorage(Context(
            config=config, server=self.get_server()
        ))
        await storage.put(iurl, IMAGE_BYTES)
        await storage.put_crypto(iurl)
        got = await storage.get_crypto(iurl)
        expect(got).not_to_be_null()
        expect(got).not_to_be_an_error()
        expect(got).to_equal("ACME-SEC")
