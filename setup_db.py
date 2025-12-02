from app import app, db, Admin, bcrypt

def setup_database(drop_first=False):
    with app.app_context():
        if drop_first:
            print('Dropping existing database tables (this will erase data)...')
            db.drop_all()
        db.create_all()

        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = Admin(username='admin', password=hashed_password, role='admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username='admin', password='admin123'")
        else:
            new_password = "admin123"
            admin.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            admin.role = 'admin'
            db.session.commit()
            print(f"Password updated for user '{admin.username}'.")
            
if __name__ == '__main__':
    setup_database(drop_first=True)
