lazy_mysql
=======

Purpose
----------

将 `lazy_mysql.py`  文件放到到项目任意目录中便可使用本模块全部功能。

本模块基于 `MySQL-python`  之上提供了四个常用对象，分别是：

* **Engine**   : 负责连接数据库，执行 SQL 语句。
* **Pool**      : 数据库连接池，负责管理 Engine 对象。
* **Table**    : 该对象映射到数据表。
* **Column** : 该对象映射到数据表字段。


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

*_engine* 参数可以接收一个 *Engine* 或 *Pool* 实例对象。

在初始化中定义数据表字段，你可以只初始化部分字段而非全部字段，**Column** 对象代表一个字段对象，实例化一个 **Column** 字段仅需要传入一个字段名称，**Column** 对象不会检查字段类型及合法性。

### 3. Select 操作

    # 实例化一个数据表对象。
    s = Schedule()
          
    # SELECT * FROM schedule LIMIT 1;
    print s.select().go() 

    # SELECT * FROM schedule;
    print s.select().limit().go()
    
    # SELECT taskName, status FROM schedule WHERE (taskId=1) LIMIT 1;
    print s.select(s.task_name, s.status).where(schedule.task_id == 1).go()


API
----

### Engine

