go#!/usr/bin/env python
# -*- coding: utf8 -*-

from lazy_mysql import Engine, Table, Column


# create engine instance in order to connect local database
engine = Engine('localhost', 'db_site_monitor', 'puppy', 'puppy')


# define Schedule object which is subclass of Table to map table 'tb_schedule_i' in database 'db_site_monitor'
class Schedule(Table):
    def __init__(self, table_name='tb_schedule_i', _engine=engine, *columns):
        """
        This class maps itself to table tb_schedule_i in database db_site_monitor hosted in local machine.
        """
        super(Schedule, self).__init__(table_name, _engine, *columns)

        self.schedule_id = Column('scheduleId')
        self.task_id = Column('taskId')
        self.task_name = Column('taskName')
        self.status = Column('status')
        self.due_datetime = Column('dueDateTime')
        self.start_datetime = Column('startDateTime')
        self.end_datetime = Column('endDateTime')
        self.edit_datetime = Column('editDateTime')


if __name__ == '__main__':
    # SHOW DATABASES
    engine.show_databases()

    # SHOW TABLES
    engine.show_tables()

    # SHOW CREATE TABLE `tb_schedule_i`
    engine.show_create_table('tb_schedule_i')

    # CREATE INSTANCE schedule
    schedule = Schedule()

    # SELECT * FROM tb_schedule_i LIMIT 1
    schedule.select().go()

    # SELECT taskName, status FROM tb_schedule_i WHERE (taskId=1) LIMIT 1
    schedule.select(schedule.task_name, schedule.status).where(schedule.task_id == 1).go()

    # SELECT DISTINCT * FROM tb_schedule_i ORDER BY dueDateTime DESC LIMIT 1, 2
    schedule.select().distinct().order(schedule.due_datetime, desc=True).limit(1, 2).go()

    # UPDATE tb_schedule_i SET status=0 WHERE (scheduleId=2 AND taskId=1) LIMIT 1
    schedule.update(**{schedule.status.name: 0}).where(schedule.schedule_id == 2, schedule.task_id == 1).go()

    # INSERT INTO tb_schedule_i SET status=1
    new_schedule_id = schedule.insert(**{schedule.status.name: 1}).go()

    # DELETE FROM tb_schedule_i WHERE (scheduleId=93) LIMIT 1
    schedule.delete().where(schedule.schedule_id == new_schedule_id).go()

    # SELECT COUNT(DISTINCT scheduleId) AS X FROM tb_schedule_i WHERE (scheduleId>50) LIMIT 1
    schedule.count(schedule.schedule_id, distinct=True).where(schedule.schedule_id > 50).go()