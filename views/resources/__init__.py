#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

# Хрень автоматом импортящая все модули в каталоге
for module in os.listdir(os.path.dirname(__file__)):
    if module == '__init__.py' or module[-3:] != '.py':
        continue
    __import__(module[:-3], locals(), globals())
del module

