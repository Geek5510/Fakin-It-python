# ======== File not used while running the final game, made to set up the database ========
import TaskDatabase

# Reading tasks from text file
file = open("Tasks.txt", "r")
data = file.read()
file.close()

# Splitting tasks into individual tasks and sorting to categories
data = data.split("\n\n")
lst = []
for category in data:
    split = category.split("\n")
    lst.append(split)

lst[2] = lst[2][:-1]  # Removing final empty space

# Checking for tasks that are too long to shorten
for category in lst:
    for task in category:
        if len(task) > 97:
            print(len(task), task)

# Connecting to / Creating the task database
task_database = TaskDatabase.TaskDatabase("task_database")
# Adding each task to the database
for point_task in lst[0]:
    task_database.add_task_point(point_task)
for number_task in lst[1]:
    task_database.add_task_number(number_task)
for raise_task in lst[2]:
    task_database.add_task_raise(raise_task)
