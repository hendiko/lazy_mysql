#!/usr/bin/env python
# -*- coding: utf8 -*-
# 2014-1-11

"""
2014-1-13 version 1.0.1.2:
    1. 修复Engine.connect()方法。

    1. Fixed bug in Engine.connect().

2014-1-13 version 1.0.1.1:
    1. 修改Engine对象接收charset作为初始化参数。

    1. Modified class Engine to accept charset as one of its __init__() arguments.

2014-1-12 version 1.0.1:
    1. Table.remove_column(self, column) 改进为column参数可以为Column对象。
    2. Engine对象增加若干方法。
    3. 增加clear()方法。
    4. 更名为lazy_mysql。

    1. Improve Table.remove_column to be able to accept Column object.
    2. Add several instance methods to Engine object.
    3. Add method clear() to _BaseSession object.
    4. Renamed module to lazy_mysql.
"""
__author__ = 'Xavier Yin'
__version__ = '1.0.1'
__date__ = '2014-1-12'