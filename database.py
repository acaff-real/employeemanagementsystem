from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean # <-- Add Boolean

import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# 1. Look for a cloud database URL. If none exists, fallback to local SQLite.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./employee_app.db")

# 2. SQLAlchemy quirk: Render uses "postgres://", but SQLAlchemy requires "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Connect differently depending on the database type
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Create the SQLite database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./employee_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Employee table
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)

    username = Column(String, unique=True, index=True) 
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    # Link to tasks
    tasks = relationship("Task", back_populates="owner")
    

# Define the Task table
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    status = Column(String, default="Not Started")
    employee_id = Column(Integer, ForeignKey("employees.id"))

    # Link back to employee
    owner = relationship("Employee", back_populates="tasks")
    comments = relationship("Comment", back_populates="task")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    author_id = Column(Integer, ForeignKey("employees.id"))

    task = relationship("Task", back_populates="comments")
    author = relationship("Employee")

# Create the tables in the database
Base.metadata.create_all(bind=engine)