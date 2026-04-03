from pydantic import BaseModel
from typing import List, Optional

# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    description: str

class TaskCreate(TaskBase):
    employee_id: int

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None

class Task(TaskBase):
    id: int
    employee_id: int
    status: str
    comments: List[Comment] = [] # <-- This is the crucial line!

    class Config:
        from_attributes = True



# --- EMPLOYEE SCHEMAS ---
class EmployeeBase(BaseModel):
    name: str
    role: str
    is_admin: bool = False

class EmployeeCreate(EmployeeBase):
    username: str
    password: str



class Employee(EmployeeBase):
    id: int
    username: str # It is okay to return the username to the frontend!
    tasks: List[Task] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    pass

class CommentAuthor(BaseModel):
    username: str
    class Config:
        from_attributes = True

class Comment(CommentBase):
    id: int
    task_id: int
    author: CommentAuthor

    class Config:
        from_attributes = True