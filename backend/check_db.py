from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
print("Tables created:", inspector.get_table_names())