# update_db.py
import os
from sqlalchemy import inspect, text
from app import create_app
from app.extensions import db

def update_db_schema(app):
    with app.app_context():
        insp = inspect(db.engine)
        if not insp.has_table("users"):
            return
        cols = [c["name"] for c in insp.get_columns("users")]
        
        renames = [
            ("usr_name", "u_name"),
            ("setka_lock", "grid_lock"),
            ("wid_cvet", "wid_clr"),
            ("wid_prozr", "wid_op"),
            ("clock_stile", "clock_stil"),
            ("weath_city", "pog_city")
        ]
        
        with db.engine.begin() as conn:
            # 1. Переименование колонок
            for old_col, new_col in renames:
                if old_col in cols and new_col not in cols:
                    print(f"Переименование колонки {old_col} в {new_col}...")
                    conn.execute(text(f"ALTER TABLE users RENAME COLUMN {old_col} TO {new_col}"))
                    print(f"Колонка {old_col} успешно переименована в {new_col}!")
            
            # Обновляем список колонок после переименования
            insp = inspect(db.engine)
            cols = [c["name"] for c in insp.get_columns("users")]
            
            # 2. Добавление новых колонок, если их нет
            new_cols = [
                ("is_fr", "BOOLEAN DEFAULT FALSE NOT NULL"),
                ("bg_sz", "VARCHAR(20) DEFAULT 'cover' NOT NULL"),
                ("bg_ps", "VARCHAR(20) DEFAULT 'center' NOT NULL")
            ]
            
            for col_name, col_sql in new_cols:
                if col_name not in cols:
                    print(f"Добавление колонки {col_name}...")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_sql}"))
                    print(f"Колонка {col_name} успешно добавлена!")
                else:
                    print(f"Колонка {col_name} уже существует.")

def update():
    app = create_app(os.environ.get("FLASK_ENV", "dev"))
    update_db_schema(app)

if __name__ == "__main__":
    update()
