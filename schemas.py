from pydantic import BaseModel, Field
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Comment Schemas (Moved up so Task can safely use them) ---
class CommentAuthor(BaseModel):
    username: str
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    task_id: int
    author: CommentAuthor

    class Config:
        from_attributes = True

# --- Task Schemas ---
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
    comments: List[Comment] = [] 

    class Config:
        from_attributes = True

# --- Employee Schemas ---
class EmployeeBase(BaseModel):
    name: str
    role: str
    is_admin: bool = False

class EmployeeCreate(EmployeeBase):
    username: str
    # Pydantic validation to reject excessively long passwords at creation
    password: str = Field(..., max_length=72)

class Employee(EmployeeBase):
    id: int
    username: str 
    tasks: List[Task] = []

    class Config:
        from_attributes = True