# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Author : Xavier Yin
# Date    : 2013-12-26

"""
本模块包括 Engine, Session, Table, Column, Pool 五个类对象。
Manipulate MySQL database in a ORM style.
目前支持SELECT, INSERT, DELETE, UPDATE, COUNT操作。
条件支持WHERE, ORDER BY (DESC), DISTINCT, LIMIT。
"""
__author__ = 'Xavier Yin'
__version__ = '1.2.2'
__date__ = '2015-3-14'


from datetime import datetime
from MySQLdb import cursors
from Queue import Queue, Full, Empty
from threading import RLock
import logging
import MySQLdb

MySQLdb.threadsafety = 1
logger = logging.getLogger(__name__)


class Engine(object):
    """The engine to connect database."""
    def __init__(self, host, schema, user, pw, port=3306, charset='utf8',
                 cursor_class='dict', autocommit=True, debug=True, *args, **kwargs):
        """初始化数据库连接参数。"""
        self.host = host
        self.schema = schema
        self.user = user
        self.pw = pw
        self.port = port
        self.connection = None
        self.charset = charset
        self._cursor_class = cursor_class
        self.autocommit = autocommit
        self.debug = debug
        self.args = args
        self.kwargs = kwargs
        self.affected_rows = 0
        self.last_executed = ''

    @property
    def cursor_class(self):
        if self._cursor_class == 'dict':
            return cursors.DictCursor
        else:
            return cursors.Cursor

    @cursor_class.setter
    def cursor_class(self, _class):
        self._cursor_class = _class

    def connect(self, cursor_class="dict"):
        """建立数据库连接。"""
        self.cursor_class = cursor_class
        if not self.connection:
            self.connection = MySQLdb.connect(
                self.host, self.user, self.pw, self.schema, port=self.port,
                charset=self.charset, cursorclass=self.cursor_class)
            self.connection.autocommit(self.autocommit)
        return self.connection

    def create_database(self, table_name, confirm=False):
        """创建新的数据库。"""
        if confirm:
            sql = 'CREATE DATABASE `%(name)s`' % {'name': table_name}
            return self._transaction(sql)

    def drop_database(self, table_name, confirm=False):
        """
        丢弃数据库
        :param table_name: 数据库名称。
        :param confirm: 安全确认。仅当confirm为True时才执行丢弃操作。
        """
        if confirm is True:
            sql = 'DROP DATABASE `%(name)s`' % {'name': table_name}
            return self._transaction(sql)

    def show_create_table(self, table_name):
        """显示数据库创建SQL语句。"""
        sql = 'SHOW CREATE TABLE `%(name)s`' % {'name': table_name}
        return self._transaction(sql, True)[0]['Create Table']

    def show_databases(self):
        """显示所有数据库名称。"""
        sql = 'SHOW DATABASES'
        return [d['Database'] for d in self._transaction(sql, True)]

    def show_tables(self):
        """显示所有数据表名称。"""
        sql = 'SHOW TABLES'
        return [d['Tables_in_%s' % self.schema] for d in self._transaction(sql, True)]

    def set_names(self, charset='utf8'):
        """设置输出字符集编码。"""
        sql = 'SET NAMES `%(name)s`' % {'name': charset.upper()}
        return self._transaction(sql)

    def _transaction(self, sql, fetch=False, cursor_class="dict"):
        """不要直接调用本方法，执行SQL语句并返回结果。"""
        self.affected_rows, self.last_executed, timestamp = 0, '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            conn = self.connect(cursor_class)
            cursor = conn.cursor()
            self.affected_rows = cursor.execute(sql)
        except Exception as e:
            logger.exception(str(e))
            self.connection = None
            conn = self.connect(cursor_class)
            cursor = conn.cursor()
            self.affected_rows = cursor.execute(sql)

        self.last_executed = cursor._last_executed
        if self.debug:
            logger.debug('%s : %s ROW(S) AFFECTED WITH SQL: %s', timestamp, self.affected_rows, self.last_executed)
        result = cursor.fetchall() if fetch else self.affected_rows
        return result


class Pool(object):

    def __init__(self, host, schema, user, pw, port=3306, charset='utf8',
                 cursor_class='dict', autocommit=True, debug=True, pool_size=2,
                 extras=4, wait_time=5, *args, **kwargs):
        """初始化数据库连接参数。"""
        self.host = host
        self.schema = schema
        self.user = user
        self.pw = pw
        self.port = port
        self.connection = None
        self.charset = charset
        self.cursor_class = cursor_class
        self.autocommit = autocommit
        self.debug = debug
        self.args = args
        self.kwargs = kwargs
        self.affected_rows, self.last_executed = 0, ''
        self.wait_time = wait_time
        self.lock = RLock()
        self.pool_size = pool_size
        self.limits = extras + self.pool_size
        self._count = 0
        self.pool = Queue(self.pool_size)

    def spawn_engine(self):
        self.lock.acquire()
        if self._count < self.limits:
            self._count += 1
            _engine = Engine(
                self.host, self.schema, self.user, self.pw, self.port, self.charset,
                self.cursor_class, self.autocommit, self.debug, *self.args, **self.kwargs)
            self.lock.release()
        else:
            self.lock.release()
            _engine = self.get()

        return _engine

    def put(self, engine=None):
        if not isinstance(engine, Engine):
            engine = self.spawn_engine()
        try:
            self.pool.put(engine, False)
        except Full:
            self.lock.acquire()
            self._count -= 1
            self.lock.release()

    def get(self):
        try:
            engine = self.pool.get(timeout=self.wait_time)
            self.pool.task_done()
            return engine
        except Empty:
            self.lock.acquire()
            if self._count < self.limits:
                self.lock.release()
                return self.spawn_engine()
            else:
                self.lock.release()
                engine = self.pool.get()
                self.pool.task_done()
                return engine


class Column(object):
    def __init__(self, name):
        """数据库字段。"""
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        name = '{0}_{1}'.format(self.name, 'eq')
        return '{0}=%({1})s'.format(self.name, name), {name: other}

    def __ne__(self, other):
        name = '{0}_{1}'.format(self.name, 'ne')
        return '{0}<>%({1})s'.format(self.name, name), {name: other}

    def __gt__(self, other):
        name = '{0}_{1}'.format(self.name, 'gt')
        return '{0}>%({1})s'.format(self.name, name), {name: other}

    def __ge__(self, other):
        name = '{0}_{1}'.format(self.name, 'ge')
        return '{0}>=%({1})s'.format(self.name, name), {name: other}

    def __lt__(self, other):
        name = '{0}_{1}'.format(self.name, 'lt')
        return '{0}<%({1})s'.format(self.name, name), {name: other}

    def __le__(self, other):
        name = '{0}_{1}'.format(self.name, 'le')
        return '{0}<=%({1})s'.format(self.name, name), {name: other}

    def like(self, other):
        name = '{0}_{1}'.format(self.name, 'like')
        return '{0} LIKE %({1})s'.format(self.name, name), {name: other}

    def in_(self, *other):
        name = '{0}_{1}'.format(self.name, 'in')
        return '{0} IN %({1})s'.format(self.name, name), {name: other}

    def between(self, floor, ceil):
        _floor = '{0}_{1}'.format(self.name, 'floor')
        _ceil = '{0}_{1}'.format(self.name, 'ceil')
        return '{0} BETWEEN %({1})s AND %({2})s'.format(self.name, _floor, _ceil), {_floor: floor, _ceil: ceil}

    def is_null(self, boolean=True):
        name = '{0}_{1}'.format(self.name, 'is_null')
        if boolean:
            return '{0} IS %({1})s'.format(self.name, name), {name: None}
        else:
            return '{0} IS NOT %({1})s'.format(self.name, name), {name: None}


class Table(object):
    """数据表对象。"""

    def __init__(self, table_name, _engine=None, *columns):
        """初始化数据表，可以在columns参数中动态传入字段名称，或者覆写本方法并在新方法中直接定义字段。"""
        self.engine = _engine
        self.table_name = table_name
        self.add_column(*columns)

    def add_column(self, *columns):
        """增加字段。"""
        for column in columns:
            setattr(self, column.name, column) if isinstance(column, Column) else setattr(self, column, Column(column))
        return self

    def remove_column(self, *columns):
        """删除字段。"""
        for column in columns:
            self.__delattr__(column.name) if isinstance(column, Column) else self.__delattr__(column)
        return self

    def binding_engine(self, engine):
        """绑定用来建立数据库连接的Engine对象。"""
        self.engine = engine
        return self

    def select(self, *columns):
        """SELECT操作。"""
        return _Select(self.engine, self.table_name, 'SELECT', *columns)

    def insert(self, **assignments):
        """INSERT操作。"""
        return _Insert(self.engine, self.table_name, 'INSERT', **assignments)

    def update(self, **assignments):
        """UPDATE操作。"""
        return _Update(self.engine, self.table_name, 'UPDATE', **assignments)

    def delete(self):
        """DELETE操作。"""
        return _Delete(self.engine, self.table_name, 'DELETE')

    def count(self, column=None, distinct=None):
        """COUNT操作。"""
        return _Count(self.engine, self.table_name, 'COUNT', column, distinct)


class _BaseSession(object):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        self.engine, self.table_name, self.action = engine, table_name, action
        self._columns, self._assignments = columns, assignments

        self._where_clause, self._where_dict = '', {}
        self._distinct_clause = self._order_clause = self._limit_clause = ''
        self.affected_rows, self.last_executed = 0, ''
        self.limit(1)   # for safety consideration

    def clear(self):
        self._where_clause, self._where_dict = '', {}
        self._distinct_clause = self._order_clause = self._limit_clause = ''
        self.limit(1)   # for safety consideration
        return self

    def distinct(self, flag=True):
        """增加DISTINCT条件。"""
        self._distinct_clause = 'DISTINCT' if flag else ''
        return self

    def where(self, *columns):
        """
        执行WHERE语句。
        :param columns: Column对象。
        """
        if columns:
            if self._where_clause:
                new_clause = '({0})'.format(' AND '.join([col[0] for col in columns]))
                self._where_clause = ' OR '.join([self._where_clause, new_clause])
            else:
                self._where_clause = 'WHERE ({0})'.format(' AND '.join([col[0] for col in columns]))
            self._where_dict.update(reduce(lambda x, y: x + y, [column[1].items() for column in columns]))
        else:
            self._where_clause, self._where_dict = '', {}
        return self

    def where_and(self, *columns):
        if columns:
            if self._where_clause:
                new_clause = '({0})'.format(' AND '.join([col[0] for col in columns]))
                self._where_clause = ' AND '.join([self._where_clause, new_clause])
            else:
                self._where_clause = 'WHERE ({0})'.format(' AND '.join([col[0] for col in columns]))
            self._where_dict.update(reduce(lambda x, y: x + y, [column[1].items() for column in columns]))
        else:
            self._where_clause, self._where_dict = '', {}
        return self

    def order(self, column=None, desc=False):
        """执行ORDER条件。"""
        self._order_clause = ('ORDER BY {0} {1}'.format(str(column), 'DESC' if desc else 'ASC')) if column else ''
        return self

    def limit(self, number=None, step=None):
        """执行LIMIT条件。"""
        self._limit_clause = '' if number is None else 'LIMIT %s' % number
        if None not in (number, step):
            self._limit_clause = '%s, %s' % (self._limit_clause, step)
        return self

    def _transaction(self, clauses, sql_dict, cursor_class):
        sql_clause = ' '.join([clause for clause in clauses if clause])
        self.affected_rows, self.last_executed, timestamp = 0, '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        _engine = self.engine.get() if isinstance(self.engine, Pool) else self.engine

        try:
            conn = _engine.connect(cursor_class)
            cursor = conn.cursor()
            self.affected_rows = cursor.execute(sql_clause, sql_dict)
        except Exception as e:
            logger.exception(str(e))
            _engine.connection = None
            conn = _engine.connect(cursor_class)
            cursor = conn.cursor()
            self.affected_rows = cursor.execute(sql_clause, sql_dict)
        finally:
            if isinstance(self.engine, Pool):
                self.engine.put(_engine)

        self.last_executed = cursor._last_executed
        if _engine.debug:
            logger.debug('%s: %s ROW(S) AFFECTED WITH SQL: %s', timestamp, self.affected_rows, self.last_executed)
        if self.action == 'SELECT':
            return cursor.fetchall()
        elif self.action == 'INSERT':
            return cursor.lastrowid
        elif self.action in ('UPDATE', 'DELETE'):
            return self.affected_rows
        elif self.action == 'COUNT':
            return cursor.fetchall()[0]['X']


class _Select(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Select, self).__init__(engine, table_name, action, *columns, **assignments)
        self._action_clause = ', '.join([str(column) for column in self._columns]) or '*'
        self._group_by_clause = None

    def group_by(self, column):
        self._group_by_clause = 'GROUP BY %s' % (str(column))
        return self

    def go(self, cursor_class="dict"):
        clauses = [self.action, self._distinct_clause, self._action_clause, 'FROM', self.table_name,
                   self._where_clause, self._group_by_clause, self._order_clause, self._limit_clause]
        sql_dict = self._where_dict
        return self._transaction(clauses, sql_dict, cursor_class)


class _Insert(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Insert, self).__init__(engine, table_name, action, *columns, **assignments)
        self._action_clause = ', '.join(['{0}=%(_insert_{0})s'.format(k) for k in self._assignments])
        self._action_dict = dict(('_insert_%s' % k, v) for k, v in self._assignments.items())

    def go(self, cursor_class="dict"):
        clauses = [self.action, 'INTO', self.table_name, 'SET', self._action_clause]
        sql_dict = self._action_dict
        return self._transaction(clauses, sql_dict, cursor_class)


class _Update(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Update, self).__init__(engine, table_name, action, *columns, **assignments)
        self._action_clause = ', '.join(['{0}=%(_update_{0})s'.format(k) for k in self._assignments])
        self._action_dict = dict(('_update_%s' % k, v) for k, v in self._assignments.items())

    def go(self, cursor_class="dict"):
        clauses = [self.action, self.table_name, 'SET', self._action_clause, self._where_clause,
                   self._order_clause, self._limit_clause]
        sql_dict = dict()
        sql_dict.update(self._action_dict, **self._where_dict)
        return self._transaction(clauses, sql_dict, cursor_class)


class _Delete(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Delete, self).__init__(engine, table_name, action, *columns, **assignments)

    def go(self, cursor_class="dict"):
        clauses = [self.action, 'FROM', self.table_name, self._where_clause, self._order_clause, self._limit_clause]
        sql_dict = self._where_dict
        return self._transaction(clauses, sql_dict, cursor_class)


class _Count(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Count, self).__init__(engine, table_name, action, *columns, **assignments)
        col, distinct = self._columns
        self._action_clause = ' '.join(['DISTINCT' if col and distinct else '', "'*'" if col is None else str(col)])
        self._action_clause = 'COUNT({0})'.format(self._action_clause)

    def go(self, cursor_class="dict"):
        clauses = ['SELECT', self._action_clause, 'AS X FROM', self.table_name, self._where_clause, self._limit_clause]
        sql_dict = self._where_dict
        return self._transaction(clauses, sql_dict, cursor_class)


if __name__ == '__main__':
    pass