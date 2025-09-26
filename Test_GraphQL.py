import os
import mysql.connector
import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------
# Database Connection
# -----------------------------
def get_mysql_connection():
    password = os.getenv("MySQL_passwd")
    if not password:
        raise ValueError("MySQL_passwd environment variable not set!")
    
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="acro0",
        password=password,
        database="TestDB",
        auth_plugin="mysql_native_password"
    )

# -----------------------------
# GraphQL Schema
# -----------------------------
@strawberry.type
class Book:
    id: int
    title: str
    author: str

@strawberry.type
class Query:
    @strawberry.field
    def books(self) -> list[Book]:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, author FROM Books")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Book(**row) for row in rows]

    @strawberry.field
    def book_by_title(self, title: str) -> Book | None:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, author FROM Books WHERE title = %s", (title,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return Book(**row) if row else None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_book(self, title: str, author: str) -> Book:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Books (title, author) VALUES (%s, %s)",
            (title, author)
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return Book(id=new_id, title=title, author=author)

    @strawberry.mutation
    def update_book(self, id: int, title: str | None = None, author: str | None = None) -> Book | None:
        conn = get_mysql_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, title, author FROM Books WHERE id = %s", (id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return None

        new_title = title if title else row["title"]
        new_author = author if author else row["author"]

        cursor.execute(
            "UPDATE Books SET title = %s, author = %s WHERE id = %s",
            (new_title, new_author, id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return Book(id=id, title=new_title, author=new_author)

    @strawberry.mutation
    def delete_book(self, id: int) -> bool:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Books WHERE id = %s", (id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return deleted

# -----------------------------
# FastAPI App
# -----------------------------
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")

# -----------------------------
# Startup Hook (Table Creation)
# -----------------------------
@app.on_event("startup")
async def startup():
    print("🚀 Starting application...")

    try:
        # Test the password loading
        password = os.getenv("MySQL_passwd")
        print(f"Password loaded: {'✅ YES' if password else '❌ NO'}")
        
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TestDB.Books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                author VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ MySQL: Table ready")
    except Exception as e:
        print(f"❌ MySQL startup error: {e}")

# -----------------------------
# Run directly with Python
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Test_GraphQL:app", host="127.0.0.1", port=8000, reload=True)