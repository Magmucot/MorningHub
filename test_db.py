from app import create_app
from app.extensions import db

app = create_app('dev')
with app.app_context():
    try:
        db.create_all()
        print("Database created.")
    except Exception as e:
        print("Error:", e)
