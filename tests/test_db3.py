from app import create_app
app = create_app('dev')
print(app.config['SQLALCHEMY_DATABASE_URI'])
