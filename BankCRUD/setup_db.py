from database import conn, cursor

def setup():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        username VARCHAR(100) PRIMARY KEY,
        password VARCHAR(255)
    )
    """)
    
    cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', 'admin123')")
        print("Default admin created: admin / admin123")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup()
