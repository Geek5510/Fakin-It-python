import sqlite3
import random


class TaskDatabase:
    """
    Class for interacting with and creating the task database. For server use
    """
    def __init__(self, database_name):
        """
        Creates new connection object of database
        :param database_name: name of database
        """
        self.database_name = database_name
        self.conn = None    # Connection to database
        self.cur = None     # SQL cursor
        self.init_database()  # Initializing the database

    def init_database(self):
        """
        Initializes the database
        """
        self.conn = sqlite3.connect(self.database_name + ".db")
        self.cur = self.conn.cursor()
        # Creating task tables, with and auto incrementing primary key for use as an id
        # Creating point task table
        sql = f"CREATE TABLE IF NOT EXISTS pointTask (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT , task TEXT)"
        self.cur.execute(sql)
        # Creating raise task table
        sql = f"CREATE TABLE IF NOT EXISTS raiseTask (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT , task TEXT)"
        self.cur.execute(sql)
        # Creating number task table
        sql = f"CREATE TABLE IF NOT EXISTS numberTask (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT , task TEXT)"
        self.cur.execute(sql)

    # == Methods to add tasks ==
    def add_task_point(self, task):
        sql = f'INSERT INTO pointTask (task) VALUES("{task}")'
        self.cur.execute(sql)
        self.conn.commit()

    def add_task_raise(self, task):
        sql = f'INSERT INTO raiseTask (task) VALUES("{task}")'
        self.cur.execute(sql)
        self.conn.commit()

    def add_task_number(self, task):
        sql = f'INSERT INTO numberTask (task) VALUES("{task}")'
        self.cur.execute(sql)
        self.conn.commit()

    # == Methods to pick a random task, returns a tuple of an id and the chosen task ==
    def task_point(self):
        sql = "SELECT COUNT(*) FROM pointTask"
        self.cur.execute(sql)
        count = self.cur.fetchall()[0][0]  # Getting the amount of tasks in the category
        rand_id = random.randint(1, count)  # Choosing a random id
        # Getting the task associated with the chosen id
        sql = f"SELECT * FROM pointTask WHERE id == {rand_id}"
        self.cur.execute(sql)
        return self.cur.fetchall()[0]

    def task_number(self):
        sql = "SELECT COUNT(*) FROM numberTask"
        self.cur.execute(sql)
        count = self.cur.fetchall()[0][0]  # Getting the amount of tasks in the category
        rand_id = random.randint(1, count)  # Choosing a random id
        # Getting the task associated with the chosen id
        sql = f"SELECT * FROM numberTask WHERE id == {rand_id}"
        self.cur.execute(sql)
        return self.cur.fetchall()[0]

    def task_raise(self):
        sql = "SELECT COUNT(*) FROM raiseTask"
        self.cur.execute(sql)
        count = self.cur.fetchall()[0][0]  # Getting the amount of tasks in the category
        rand_id = random.randint(1, count)  # Choosing a random id
        # Getting the task associated with the chosen id
        sql = f"SELECT * FROM raiseTask WHERE id == {rand_id}"
        self.cur.execute(sql)
        return self.cur.fetchall()[0]


def main():
    # Test program
    t_db = TaskDatabase("task_database")
    print(t_db.task_point())
    print(t_db.task_number())
    print(t_db.task_raise())


if __name__ == '__main__':
    main()
