from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import database, schemas
from fastapi.responses import FileResponse 
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

# Initialize the app
app = FastAPI(title="Employee Management System")

# --- SECURITY SETUP ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# JWT Configuration
SECRET_KEY = "my-super-secret-development-key" # In a real app, this is a hidden environment variable!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    # Set the token to expire in 30 minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Create the secure, encoded token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


app.mount("/static", StaticFiles(directory="static"), name="static")
# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decode the wristband
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # 2. Find the user in the database
    user = db.query(database.Employee).filter(database.Employee.username == username).first()
    if user is None:
        raise credentials_exception
        
    # 3. Return the fully authenticated user object!
    return user

def get_admin_user(current_user: database.Employee = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Sudo privileges required.")
    return current_user
# --- ROUTES ---

# Create Employee (ADMIN ONLY)
@app.post("/employees/", response_model=schemas.Employee)
def create_employee(
    employee: schemas.EmployeeCreate, 
    db: Session = Depends(get_db),
    admin: database.Employee = Depends(get_admin_user) # <-- Strict bouncer!
):
    db_user = db.query(database.Employee).filter(database.Employee.username == employee.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    hashed_pwd = get_password_hash(employee.password)
    db_employee = database.Employee(
        name=employee.name, role=employee.role, username=employee.username, 
        hashed_password=hashed_pwd, is_admin=employee.is_admin
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

# Delete Employee (ADMIN ONLY)
@app.delete("/employees/{employee_id}")
def delete_employee(
    employee_id: int, 
    db: Session = Depends(get_db),
    admin: database.Employee = Depends(get_admin_user) # <-- Strict bouncer!
):
    db_employee = db.query(database.Employee).filter(database.Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(db_employee)
    db.commit()
    return {"message": "Employee deleted"}

@app.get("/employees/", response_model=list[schemas.Employee])
def get_dashboard(db: Session = Depends(get_db)):
    # Retrieves all employees and automatically includes their tasks
    return db.query(database.Employee).all()

@app.post("/tasks/", response_model=schemas.Task)
def create_task(
    task: schemas.TaskCreate, 
    db: Session = Depends(get_db),
    current_user: database.Employee = Depends(get_current_user) # <-- The Bouncer checks the ID!
):
    # --- NEW: Security Check ---
    # If they are NOT an admin, and they are NOT assigning the task to themselves: Block it.
    if not current_user.is_admin and current_user.id != task.employee_id:
        raise HTTPException(status_code=403, detail="Not authorized to assign tasks to other employees.")

    # Proceed as normal...
    db_employee = db.query(database.Employee).filter(database.Employee.id == task.employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db_task = database.Task(description=task.description, employee_id=task.employee_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(database.Task).filter(database.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update only the fields that were provided
    if task_update.description is not None:
        db_task.description = task_update.description
    if task_update.status is not None:
        db_task.status = task_update.status
        
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/", response_class=FileResponse)
def serve_webpage():
    return FileResponse("index.html")

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(database.Employee).filter(database.Employee.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # --- NEW: Generate the real JWT token ---
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.Employee)
def read_users_me(current_user: database.Employee = Depends(get_current_user)):
    # Notice we don't query the database here. 
    # The 'get_current_user' bouncer already did the work and handed us the user!
    return current_user


@app.post("/setup", response_model=schemas.Employee)
def create_first_admin(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    # Check if ANY users exist
    if db.query(database.Employee).count() > 0:
        raise HTTPException(status_code=403, detail="Setup already complete. Cannot use this route.")
        
    hashed_pwd = get_password_hash(employee.password)
    db_employee = database.Employee(
        name=employee.name, 
        role=employee.role, 
        username=employee.username, 
        hashed_password=hashed_pwd,
        is_admin=True # <-- Force the first user to be an admin
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@app.post("/tasks/{task_id}/comments", response_model=schemas.Comment)
def add_comment(
    task_id: int, 
    comment: schemas.CommentCreate, 
    db: Session = Depends(get_db), 
    current_user: database.Employee = Depends(get_current_user)
):
    db_task = db.query(database.Task).filter(database.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_comment = database.Comment(
        text=comment.text, 
        task_id=task_id, 
        author_id=current_user.id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment