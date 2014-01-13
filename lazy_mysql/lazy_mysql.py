#!/usr/bin/env python
# -*- coding: utf8 -*-
# 2014-1-11

__author__ = 'Xavier Yin'
__version__ = '1.0.1'
__date__ = '2014-1-12'


import MySQLdb
from MySQLdb import cursors
from datetime import datetime
MySQLdb.threadsafety = 1


class Engine(object):
    """The engine to connect database."""
    def __init__(self, host, schema, user, pw, charset='utf8', *args, **kwargs):
        """初始化数据库连接参数。"""
        self.host = host
        self.schema = schema
        self.user = user
        self.pw = pw
        self.charset = charset
        self.args = args
        self.kwargs = kwargs

    def connect(self, cursor_type=dict):
        """建立数据库连接。"""
        cursor_class = cursors.DictCursor if cursor_type == dict else cursors.Cursor
        conn = MySQLdb.connect(self.host, self.user, self.pw, self.schema, charset=self.charset, cursorclass=cursor_class)
        conn.autocommit(True)
        return conn

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

    def _transaction(self, sql, fetch=False, cursor_type=dict):
        """不要直接调用本方法，执行SQL语句并返回结果。"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.connect(cursor_type) as cursor:
            number = cursor.execute(sql)
            print '{0} : {1} ROW(S) AFFECTED BY SQL :'.format(timestamp, number), cursor._last_executed
            return cursor.fetchall() if fetch else number


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


class Table(object):
    """数据表对象。"""

    def __init__(self, table_name, _engine=None, *columns):
        """初始化数据表，可以在columns参数中动态传入字段名称，或者覆写本方法并在新方法中直接定义字段。"""
        self.engine = _engine
        self.table_name = table_name
        for column in columns:
            self.add_column(column)

    def add_column(self, column):
        """增加字段。"""
        setattr(self, column.name, column) if isinstance(column, Column) else setattr(self, column, Column(column))

    def remove_column(self, column):
        """删除字段。"""
        self.__delattr__(column.name) if isinstance(column, Column) else self.__delattr__(column)

    def binding_engine(self, engine):
        """绑定用来建立数据库连接的Engine对象。"""
        self.engine = engine

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
            self._where_dict.update(reduce(lambda x, y: x+y, [column[1].items() for column in columns]))
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

    def _transaction(self, clauses, sql_dict, cursor_type):
        sql_clause = ' '.join([clause for clause in clauses if clause])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.engine.connect(cursor_type) as cursor:
            number = cursor.execute(sql_clause, sql_dict)
            print '{1} : {0} ROW(S) AFFECTED BY SQL :'.format(number, timestamp), cursor._last_executed
            if self.action == 'SELECT':
                return cursor.fetchall()
            elif self.action == 'INSERT':
                return cursor.lastrowid
            elif self.action in ('UPDATE', 'DELETE'):
                return number
            elif self.action == 'COUNT':
                return cursor.fetchall()[0]['X']


class _Select(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Select, self).__init__(engine, table_name, action, *columns, **assignments)
        self._action_clause = ', '.join([str(column) for column in self._columns]) or '*'

    def go(self, cursor_type=dict):
        clauses = [self.action, self._distinct_clause, self._action_clause, 'FROM', self.table_name,
                   self._where_clause, self._order_clause, self._limit_clause]
        sql_dict = self._where_dict
        return self._transaction(clauses, sql_dict, cursor_type)


class _Insert(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Insert, self).__init__(engine, table_name, action, *columns, **assignments)
        self._action_clause = ', '.join(['{0}=%(_insert_{0})s'.format(k) for k in self._assignments])
        self._action_dict = dict(('_insert_%s' % k, v) for k, v in self._assignments.items())

    def go(self, cursor_type=dict):
        clauses = [self.action, 'INTO', self.table_name, 'SET', self._action_clause]
        sql_dict = self._action_dict
        return self._transaction(clauses, sql_dict, cursor_type)


class _Update(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Update, self).__init__(engine, table_name, action, *columns, **assignments)
        self._action_clause = ', '.join(['{0}=%(_update_{0})s'.format(k) for k in self._assignments])
        self._action_dict = dict(('_update_%s' % k, v) for k, v in self._assignments.items())

    def go(self, cursor_type=dict):
        clauses = [self.action, self.table_name, 'SET', self._action_clause, self._where_clause,
                   self._order_clause, self._limit_clause]
        sql_dict = dict()
        sql_dict.update(self._action_dict, **self._where_dict)
        return self._transaction(clauses, sql_dict, cursor_type)


class _Delete(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Delete, self).__init__(engine, table_name, action, *columns, **assignments)

    def go(self, cursor_type=dict):
        clauses = [self.action, 'FROM', self.table_name, self._where_clause, self._order_clause, self._limit_clause]
        sql_dict = self._where_dict
        return self._transaction(clauses, sql_dict, cursor_type)


class _Count(_BaseSession):
    def __init__(self, engine, table_name, action, *columns, **assignments):
        super(_Count, self).__init__(engine, table_name, action, *columns, **assignments)
        col, distinct = self._columns
        self._action_clause = ' '.join(['DISTINCT' if col and distinct else '', "'*'" if col is None else str(col)])
        self._action_clause = 'COUNT({0})'.format(self._action_clause)

    def go(self, cursor_type=dict):
        clauses = ['SELECT', self._action_clause, 'AS X FROM', self.table_name, self._where_clause, self._limit_clause]
        sql_dict = self._where_dict
        return self._transaction(clauses, sql_dict, cursor_type)


# ---------------------------------- SQLite3 --------------------------------------
import sqlite3


class SQLiteEngine(object):
    def __init__(self, db=':memory:'):
        self.db = db

    def connect(self, *args, **kwargs):
        return sqlite3.connect(self.db)

    def show_tables(self):
        sql = "SELECT name FROM sqlite_master WHERE type='table'"
        return self._transaction(sql, fetch=True)

    def show_create_table(self, table_name):
        sql = "SELECT sql FROM sqlite_master WHERE type='table' AND name=:table"
        result = self._transaction(sql, {'table': table_name}, True)
        return result[0].get('sql', []) if result else result

    def _transaction(self, sql, params_dict={}, fetch=False, cursor_type=dict):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.db)
        if cursor_type == dict:
            conn.row_factory = lambda cursor, row: dict([(col[0], row[idx]) for idx, col in enumerate(cursor.description)])
        cursor = conn.cursor()
        cursor.execute(sql, params_dict)
        print '{0} : {1} ROW(S) AFFECTED BY SQL :'.format(timestamp, cursor.rowcount), sql
        result = cursor.fetchall() if fetch else cursor.rowcount
        conn.close()
        return result

# ---------------------------------------------------------------------------------

if __name__ == '__main__':
    pass