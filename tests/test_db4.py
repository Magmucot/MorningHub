from app import create_app
app = create_app('dev')
print(app.config.get('SQLALCHEMY_DATABASE_URI'))
print(app.config.get('SQLALCHEMY_DB_URI'))
import os
print(os.environ.get('DB_URL'))
