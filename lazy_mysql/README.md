lazy_mysql
=======

TOC
-----

1. [Intro](#intro)
2. [Installation](#installation)
3. [Tutorial](#tutorial)
4. [API](#api)
    1. [Engine](#engine)
    2. [Pool](#pool)
    3. [Column](#column)
    4. [Table](#table)
    
Intro
------

本模块基于 `MySQL-python`  之上提供了四个常用对象，分别是：

* **Engine**   : 负责连接数据库，执行 SQL 语句。
* **Pool**      : 数据库连接池，负责管理 Engine 对象。
* **Table**    : 该对象映射到数据表。
* **Column** : 该对象映射到数据表字段。


Installation
--------------

从 [GitHub](https://github.com/hendiko/PyLazy.git) 下载。

    git clone https://github.com/hendiko/PyLazy.git
    
或者直接下载 `lazy_mysql.py` 文件，将 `lazy_mysql.py` 文件放到项目中任意可导入目录均可。


Tutorial
---------

### 1. 建立数据库连接

使用 **Engine** 对象连接数据库。

    from lazy_mysql import Engine, Pool, Table, Column
    
    engine = Engine('localhost', 'test', 'root', 'root')
    
如果要应付多线程多并发连接，可使用 **Pool** 对象来管理数据库连接，**Pool** 的作用是提供一个连接池，用以管理多个 **Engine** 对象。

    pool = Pool('localhost', 'test', 'root', 'root', pool_size=4, extras=4)
    
### 2. 建立 Table 类

新建一个 **Table** 对象来映射数据表，只需要新建一个类继承自 **Table** 类。

    class Schedule(Table):
    
        def __init__(self, table_name='schedule', _engine=engine, *columns):
            super(Schedule, self).__init__(table_name, _engine, *columns)
            
            self.schedule_id = Column('scheduleId')
            self.task_id = Column('taskId')
            self.task_name = Column('taskName')
            self.status = Column('status')

_engine 参数可以接收一个 *Engine* 或 *Pool* 实例对象。

在初始化中定义数据表字段，你可以只初始化部分字段而非全部字段，**Column** 对象代表一个字段对象，实例化一个 **Column** 字段仅需要传入一个字段名称，**Column** 对象不会检查字段类型及合法性。

### 3. Select 操作

    # 实例化一个数据表对象。
    s = Schedule()
          
    # SELECT * FROM schedule LIMIT 1;
    s.select().go() 

    # SELECT * FROM schedule;
    s.select().limit().go()
    
    # SELECT taskName, status FROM schedule WHERE (taskId=1) LIMIT 1;
    s.select(s.task_name, s.status).where(schedule.task_id == 1).go()
    
    # SELECT DISTINCT taskName FROM schedule WHERE (scheduleId=1) GROUP BY taskName ORDER BY taskId DESC LIMIT 1, 4;
    s.select(s.task_name).where(s.schedule_id == 1).distinct().order(s.task_id, desc=True).group_by(s.task_name).limit(1, 4).go()
    
    # SELECT * FROM schedule WHERE (scheduleId=1 AND taskId=2) OR (taskId=2) AND (taskName='query') LIMIT 1;
    s.select().where(s.schedule_id == 1, s.task_id == 3).where(s.task_id == 2).where_and(s.task_name == "query").go()
    
### 4. Insert 操作

    # INSERT INTO schedule SET taskName='query';
    s.insert(**{s.task_name.name: 'query'}).go()
    
    # 或者
    s.insert(taskName="query").go()
    
### 5. Update 操作

    # UPDATE schedule SET taskName='query2' WHERE (scheduleId=5) LIMIT 1;
    s.update(**{s.task_name.name: "query2"}).where(s.schedule_id == 5).go()

    # 或者
    s.update(taskName="query2").where(s.schedule_id == 5).go()
    
### 6. Delete 操作

    # DELETE FROM schedule WHERE (scheduleId=5) LIMIT 1;
    s.delete().where(s.schedule_id == 5).go()
    
### 7. Count 操作

    # SELECT COUNT(DISTINCT scheduleId) AS X FROM schedule WHERE (scheduleId>2) LIMIT 1;
    s.count(s.schedule_id, distinct=True).where(s.schedule_id > 2).go()


API
----

### 1. Engine

**Engine** 对象负责数据库连接，执行 SQL 语句。

#### 1.1. \__init\__(self, host, schema, user, pw, port=3306, charset='utf8', cursor_class='dict', autocommit=True, debug=True, \*args, \*\*kwargs):

* host: 数据库主机
* schema: 数据库名称。
* user: 用户名。
* pw: 密码。
* port: 端口。
* charset: 字符集。
* cursor_class: 游标类型，默认值为 'dict'，其他均返回 tuple 类型的结果集。
* autocommit: 自动提交。
* debug: 调试模式，若为真，则打印 SQL 语句。
* args: 其他 MySQLdb.connect() 参数。
* kwargs: 其他 MySQLdb.connect() 参数。

#### 1.2. affected_rows

执行 SQL 语句影响的数据表行数。

#### 1.3. last_executed

最后一次成功执行的 SQL 语句。

#### 1.4. cursor_class

数据库连接游标类型。如果 `cursor_class='dict'`，则使用 DictCursor，否则使用 Cursor。

#### 1.5. connect(self, cursor_class=None)

返回 **Connection** 对象，连接数据库，如果 cursor_class 为 None，则使用默认的 self.cursor_class 属性进行连接。

#### 1.6. close(self)

关闭 **Connection** 对象。


### 2. Pool

#### 2.1. \__init\__(self, host, schema, user, pw, port=3306, charset='utf8', cursor_class='dict', autocommit=True, debug=True, pool_size=2, extras=4, wait_time=5, \*args, \*\*kwargs):

初始化连接池，用以管理 **Engine** 对象。**Pool** 内部有一个保存 **Engine** 对象的队列 **self.pool**。Pool 允许在连接池外额外创建一些 Engine 对象用以应付超出预期的请求数量。

**Pool** 初始化参数与 **Engine** 初始化参数大部分相同。

* pool_size: 设置连接池大小。
* extras: 当连接池满时，允许额外创建的 **Engine** 对象最大数量。
* wait_time: 当连接池为空时，等待获取 **Engine** 的超时时间。

#### 2.2. count

当前所有 **Engine** 对象数量。

#### 2.3. put(self, engine=None)

回收 **Engine** 对象到连接池。

#### 2.4. get(self)

从连接池申请 **Engine** 对象。

#### 2.5. spawn_engine(self):

创建新的 **Engine** 对象。

### 3. Column

数据库字段对象。

#### 3.1. \__init\__(self, name)

参数 *name* 为数据库字段名称。

#### 3.2. like(self, other)

实现 SQL LIKE 语句。

#### 3.3. in_(self, \*other)

实现 SQL IN 语句。

#### 3.4. between(self, floor, ceil)

实现 SQL BETWEEN 语句。

#### 3.5. is_null(self, boolean=True)

实现 SQL IS NULL 或 IS NOT NULL 语句。

### 4. Table

#### 4.1. \__init\__(self, table_name, \_engine=None, \*columns)

实例化 **Table** 对象。

* table_name: 数据表名称。
* \_engine: 支持传入 **Engine** 或 **Pool** 对象。

#### 4.2. add_column(self, \*columns)

向 Table 添加字段属性。

#### 4.3. remove_column(self, \*columns)

从 Table 删除字段属性。

#### 4.4. binding_engine(self, engine)

重新绑定数据表的 engine 属性，参数 *engine* 支持传入 **Engine** 或 **Pool** 对象。

#### 4.5. select(self, \*columns)

执行 SELECT 语句。

#### 4.6. insert(self, \**assignments)

执行 INSERT 语句。

#### 4.7. update(self, \**assignments)

执行 UPDATE 语句。

#### 4.8 delete(self)

执行 DELETE 语句。

#### 4.9. count(self, column=None, distinct=None)

执行 COUNT 语句。


