from sqlalchemy import create_engine
engine = create_engine('sqlite:////home/magus/code/projects/MorningHub/db/morninghub_dev.db')
engine.connect()
print("Success")
