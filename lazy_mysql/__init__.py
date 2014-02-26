#!/usr/bin/env python
# -*- coding: utf8 -*-
# 2014-1-11

"""
2014-1-12 version 1.0.1.0:
    1. Table.remove_column(self, column) 改进为column参数可以为Column对象。
    2. Engine对象增加若干方法。
    3. 增加clear()方法。
    4. 更名为lazy_mysql。

    1. Improve Table.remove_column to be able to accept Column object.
    2. Add several instance methods to Engine object.
    3. Add method clear() to _BaseSession object.
    4. Renamed module to lazy_mysql.

2014-1-13 version 1.0.1.1:
    1. 修改Engine对象接收charset作为初始化参数。

    1. Modified class Engine to accept charset as one of its __init__() arguments.

2014-1-13 version 1.0.1.2:
    1. 修复Engine.connect()方法。

    1. Fixed bug in Engine.connect().

2014-1-16 version 1.0.2.0:
    1. 增加SQL执行日志。
    2. 增加Session的affected_rows, last_executed属性。

    1. Added logger, all sql execution would be logged at debug level.
    2. Added property affected_rows, last_executed to _BaseSession and Engine object.

2014-1-16 version 1.0.2.1:
    1. 使Table.binding_engine()方法具有返回值。

    1. Making Table.binding_engine() method return itself.

2014-1-16 version 1.0.3.0:
    1. 修改Table.add_column，Table.remove_column方法签名。

    1. Change signature of Table.add_column, Table.remove_column.

2014-2-22 version 1.1.0:
    1. Column对象增加is_null()方法，支持MYSQL的IS NULL语句。

    1. Improved object Column by adding method is_null() in order to support MySql syntax IS NULL.

2014-2-26 version 1.1.1:
    1. 修改Session执行日志级别，SELECT, COUNT操作属于DEBUG级别，INSERT, UPDATE, DELETE属于INFO级别。

    1. Reset logging level of SELECT, COUNT operations to DEBUG, logging level of INSERT, UPDATE, DELETE operations to INFO.
"""
__author__ = 'Xavier Yin'
__version__ = '1.1.1'
__date__ = '2014-2-26'