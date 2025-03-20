import os
from app import app, db

# Delete the existing database file if it exists
db_file = 'instance/study_materials.db'
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Deleted existing database: {db_file}")

# Create all tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")
