# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2020 Eka Cahya Pratama <ekapratama93@gmail.com>

from os.path import join, abspath, dirname


IMAGE_PATH = join(abspath(dirname(__file__)), 'image.png')
with open(IMAGE_PATH, 'rb') as img:
    IMAGE_BYTES = img.read()
