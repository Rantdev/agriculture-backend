import oracledb
import hashlib

dsn = 'localhost:1521/XE'
user = 'AGRICULTURE'
pw = 'Rantdev'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_connection():
    try:
        oracledb.init_oracle_client()
    except:
        pass
    
    try:
        con = oracledb.connect(user=user, password=pw, dsn=dsn)
        return con
    except oracledb.DatabaseError as e:
        raise Exception(f"Oracle Error: {e}")
    except Exception as e:
        raise Exception(f"Connection failed: {e}")

def init_database():
    """Create users table if it doesn't exist"""
    try:
        con = create_connection()
        cur = con.cursor()
        
        # Check if table exists
        cur.execute("""
            SELECT table_name FROM user_tables WHERE table_name='USERS'
        """)
        
        if not cur.fetchone():
            # Create users table
            cur.execute("""
                CREATE TABLE users (
                    user_id NUMBER PRIMARY KEY,
                    username VARCHAR2(50) UNIQUE NOT NULL,
                    password VARCHAR2(100) NOT NULL,
                    email VARCHAR2(100),
                    created_date DATE DEFAULT SYSDATE
                )
            """)
            
            # Create sequence
            cur.execute("CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1")
            con.commit()
            print("✓ Tables created successfully")
        
        con.close()
    except Exception as e:
        print(f"Database init error: {e}")

def register_user(username, password, email):
    try:
        con = create_connection()
        cur = con.cursor()
        hashed_pw = hash_password(password)
        
        cur.execute("""
            INSERT INTO users (user_id, username, password, email)
            VALUES (users_seq.NEXTVAL, :username, :password, :email)
        """, {'username': username, 'password': hashed_pw, 'email': email})
        
        con.commit()
        con.close()
        return True, "Registration successful"
    except Exception as e:
        return False, str(e)

def authenticate_user(username, password):
    try:
        con = create_connection()
        cur = con.cursor()
        hashed_pw = hash_password(password)
        
        cur.execute("""
            SELECT user_id, username, email FROM users 
            WHERE username = :username AND password = :password
        """, {'username': username, 'password': hashed_pw})
        
        result = cur.fetchone()
        con.close()
        
        if result:
            return True, {'user_id': result[0], 'username': result[1], 'email': result[2]}
        else:
            return False, "Invalid credentials"
    except Exception as e:
        return False, str(e)
