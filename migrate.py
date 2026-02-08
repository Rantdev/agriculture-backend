"""
Oracle Database Migration Script
Creates the USERS table for authentication.
Run this once before starting the backend.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_users_table():
    """Create USERS table in Oracle."""
    try:
        import oracledb
        
        dsn = os.getenv('ORACLE_DSN', 'localhost:1521/XE')
        user = os.getenv('ORACLE_USER', 'AGRICULTURE')
        password = os.getenv('ORACLE_PASSWORD', 'Rantdev')
        
        print(f'Connecting to Oracle ({dsn}) as {user}...')
        
        # Connect to Oracle
        con = oracledb.connect(user=user, password=password, dsn=dsn)
        cursor = con.cursor()
        
        # Check if USERS table already exists
        cursor.execute("""
            SELECT COUNT(*) FROM user_tables WHERE table_name='USERS'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if table_exists:
            print('✓ USERS table already exists.')
            cursor.close()
            con.close()
            return True
        
        # Create USERS table
        print('Creating USERS table...')
        cursor.execute("""
            CREATE TABLE USERS (
                user_id NUMBER PRIMARY KEY,
                username VARCHAR2(100) NOT NULL UNIQUE,
                password VARCHAR2(255) NOT NULL,
                email VARCHAR2(255) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT SYSDATE,
                updated_at TIMESTAMP DEFAULT SYSDATE
            )
        """)
        
        # Create sequence for user_id auto-increment
        print('Creating sequence for user_id...')
        cursor.execute("""
            CREATE SEQUENCE users_seq
            START WITH 1
            INCREMENT BY 1
            NOCACHE
        """)
        
        # Create trigger for auto-increment
        print('Creating trigger for auto-increment...')
        cursor.execute("""
            CREATE TRIGGER users_trigger
            BEFORE INSERT ON USERS
            FOR EACH ROW
            BEGIN
                SELECT users_seq.NEXTVAL INTO :new.user_id FROM DUAL;
            END;
        """)
        
        # Create index on username
        print('Creating index on username...')
        cursor.execute("""
            CREATE INDEX idx_users_username ON USERS(username)
        """)
        
        con.commit()
        cursor.close()
        con.close()
        
        print('✓ USERS table and related objects created successfully!')
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        return False

if __name__ == '__main__':
    success = create_users_table()
    sys.exit(0 if success else 1)
