lazy_mysql [Chinese](./README.CH.md)
==========================

<br>

TOC
-----

1. [Intro](#intro)
2. [Installation](#installation)
3. [Tutorial](#tutorial)
4. [API](#api)
    1. [Engine](#1-engine)
    2. [Pool](#2-pool)
    3. [Column](#3-column)
    4. [Table](#4-table)

<br>

Intro
------

The module which is based on `MySQL-python` provides four main classes:

* **Engine**   : connect to MySQL server and execute SQL statements.
* **Pool**      : a pool that manages Engine objects.
* **Table**    : a python object mapping table in database.
* **Column** : a python object mapping field in database. 

### Dependencies

* Python 2.6 - 2.7
* MySQLdb-python 1.2.3+

<br>

Installation
--------------

Download from [GitHub](https://github.com/hendiko/PyLazy.git).

    git clone https://github.com/hendiko/PyLazy.git

Or you can simply download `lazy_mysql.py` then put it anywhere in your project.
   
<br>

Tutorial
---------

### 1. Connect to server

Use **Engine**.

    from lazy_mysql import Engine, Pool, Table, Column
    
    engine = Engine('localhost', 'test', 'root', 'root')
   
It had better use **Pool** object to set up a pool to manage **Engine** objects to handle multi threads.

    pool = Pool('localhost', 'test', 'root', 'root', pool_size=4, extras=4)    

### 2. Create **Table** object

To create a **Table** object which maps a table in database, you need to define a class which inherits class **Table**.

    class Schedule(Table):
    
        def __init__(self, table_name='schedule', _engine=engine, *columns):
            super(Schedule, self).__init__(table_name, _engine, *columns)
            
            self.schedule_id = Column('scheduleId')
            self.task_id = Column('taskId')
            self.task_name = Column('taskName')
            self.status = Column('status')

The argument of **_engine** could be either an **Engine** instance or a **Pool** instance.

You could only define those fields you need to use instead of all of the fields that exsits in your database table. A **Column** object needs to be passed in field name to initialize itself, it won't check the field type nor validate the value to be written into database.

### 3. Select

    # Create a Table instance.
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

### 4. Insert

    # INSERT INTO schedule SET taskName='query';
    s.insert(**{s.task_name.name: 'query'}).go()
    
    # or a deprecated way which is more convenient but less reliable.
    s.insert(taskName="query").go()
    

### 5. Update

    # UPDATE schedule SET taskName='query2' WHERE (scheduleId=5) LIMIT 1;
    s.update(**{s.task_name.name: "query2"}).where(s.schedule_id == 5).go()

    # or a deprecated way which is more convenient but less reliable.
    s.update(taskName="query2").where(s.schedule_id == 5).go()
    

### 6. Delete

    # DELETE FROM schedule WHERE (scheduleId=5) LIMIT 1;
    s.delete().where(s.schedule_id == 5).go()
    

### 7. Count

    # SELECT COUNT(DISTINCT scheduleId) AS X FROM schedule WHERE (scheduleId>2) LIMIT 1;
    s.count(s.schedule_id, distinct=True).where(s.schedule_id > 2).go()


API
----

### 1. Engine

**Engine** - connect to MySQL server and execute SQL statements.

#### 1.1. \__init\__(self, host, schema, user, pw, port=3306, charset='utf8', cursor_class='dict', autocommit=True, debug=True, \*args, \*\*kwargs):

* host: host address.
* schema: database name.
* user: user name.
* pw: password.
* port: port.
* charset: charset.
* cursor_class: use DictCursor if 'dict' given, or Cursor.
* autocommit: automatically commit.
* debug: if true, log the every SQL statement executed.
* args: other arguments for MySQLdb.connect()
* kwargs: other keyword arguments for MySQLdb.connect().

#### 1.2. affected_rows

The number of rows that have been affected by executing SQL statement.

#### 1.3. last_executed

The last SQL statement that is executed successfully.

#### 1.4. cursor_class

if a string 'dict' was given, use `DictCursor` instead of `Cursor`.

#### 1.5. connect(self, cursor_class=None)

Return a **Connection** object. If *cursor_class* is *None*, the `self.cursor_class` will be used.

#### 1.6. close(self)

Close connection.

### 2. Pool

#### 2.1. \__init\__(self, host, schema, user, pw, port=3306, charset='utf8', cursor_class='dict', autocommit=True, debug=True, pool_size=2, extras=4, wait_time=5, \*args, \*\*kwargs):

Initialize a **Pool** object to manage a number of **Engine** objects. A queue object that exsits inside the **Pool** object actually reserves all **Engine** objects. You could use the parameter **pool_size** to limit the number of **Engine** in pool. It also allows you to create a number of extra **Engine** objects outside the pool, the extra engines would cost more because they are created on the fly and be destroyed after use, you probably want to use them only in case there are many requests coming suddenly.

The most of arguments of Pool is similar to those in Engine.

* pool_size: the maximum number of engines reserved in pool.
* extras: the maximun number of engines existing outside the pool.
* wait_time: the timeout seconds waiting for Engine to be acquired from the pool.

#### 2.2. count

The current number of Engines both inside or outside the pool.

#### 2.3. put(self, engine=None)

Put the Engine object back to the pool.

#### 2.4. get(self)

Acquire Engine object from the pool.

#### 2.5. spawn_engine(self):

Create a new Engine object.

### 3. Column

#### 3.1. \__init\__(self, name)

The argument name is a string that is name of field in database.

#### 3.2. like(self, other)

The like statement in SQL.

#### 3.3. in_(self, \*other)

The in statement in SQL.

#### 3.4. between(self, floor, ceil)

The between statement in SQL.

#### 3.5. is_null(self, boolean=True)

The IS NULL or IS NOT NULL in SQL.


### 4. Table

#### 4.1. \__init\__(self, table_name, \_engine=None, \*columns)

Initialize a **Table** object.

* table_name: a string that is the name of table.
* \_engine: either an **Engine** object or a **Pool** object.

#### 4.2. add_column(self, \*columns)

Add a column into Table object.

#### 4.3. remove_column(self, \*columns)

Remove a column from Table object.

#### 4.4. binding_engine(self, engine)

Binding either an Engine or a Pool object to this Table object.

#### 4.5. select(self, \*columns)

Execute SELECT statement.

#### 4.6. insert(self, \**assignments)

Execute INSERT statement.

#### 4.7. update(self, \**assignments)

Execute UPDATE statement.

#### 4.8 delete(self)

Execute DELETE statement.

#### 4.9. count(self, column=None, distinct=None)

Execute COUNT statement.