from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import conn, cursor

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="my-premium-bank-secret")

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# DEPENDENCIES (AUTH)
# =========================

def get_current_admin(request: Request):
    if request.session.get("role") != "admin":
        return False
    return True

def get_current_customer(request: Request):
    if request.session.get("role") != "customer":
        return False
    return True

# =========================
# SETUP DB ROUTE
# =========================
@app.get("/setup_db")
def setup_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        username VARCHAR(100) PRIMARY KEY,
        password VARCHAR(255)
    )
    """)
    cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', 'admin123')")
    conn.commit()
    return {"message": "Database setup complete."}


# =========================
# AUTH ROUTES
# =========================

@app.get("/login")
def login_page(request: Request, error: str = None, role: str = None):
    # If already logged in, redirect to respective dashboard
    if request.session.get("role") == "admin":
        return RedirectResponse(url="/", status_code=303)
    elif request.session.get("role") == "customer":
        return RedirectResponse(url="/customer_dashboard", status_code=303)
        
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"view": "login", "error": error, "role": role}
    )

@app.post("/login/admin")
def login_admin(request: Request, username: str = Form(...), password: str = Form(...)):
    cursor.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
    admin = cursor.fetchone()
    
    if admin:
        request.session["role"] = "admin"
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=303)
    
    return RedirectResponse(url="/login?error=Invalid%20Admin%20Credentials&role=admin", status_code=303)

@app.post("/login/customer")
def login_customer(request: Request, holder: str = Form(...), pin: str = Form(...)):
    cursor.execute("SELECT * FROM accounts WHERE account_holder = %s AND pin = %s", (holder, pin))
    account = cursor.fetchone()
    
    if account:
        request.session["role"] = "customer"
        request.session["user"] = holder
        return RedirectResponse(url="/customer_dashboard", status_code=303)
        
    return RedirectResponse(url="/login?error=Invalid%20Customer%20Credentials&role=customer", status_code=303)

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


# =========================
# CUSTOMER ROUTES
# =========================

@app.get("/customer_dashboard")
def customer_dashboard(request: Request, msg: str = None, error: str = None):
    if not get_current_customer(request):
        return RedirectResponse(url="/login", status_code=303)
        
    holder = request.session.get("user")
    cursor.execute("SELECT * FROM accounts WHERE account_holder = %s", (holder,))
    account = cursor.fetchone()
    
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"view": "customer_dashboard", "account": account, "msg": msg, "error": error}
    )

@app.post("/customer/deposit")
def customer_deposit(request: Request, amount: float = Form(...)):
    if not get_current_customer(request):
        return RedirectResponse(url="/login", status_code=303)
    holder = request.session.get("user")
    if amount > 0:
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_holder = %s", (amount, holder))
        conn.commit()
        return RedirectResponse(url="/customer_dashboard?msg=Deposit%20Successful", status_code=303)
    return RedirectResponse(url="/customer_dashboard?error=Invalid%20Amount", status_code=303)

@app.post("/customer/withdraw")
def customer_withdraw(request: Request, amount: float = Form(...)):
    if not get_current_customer(request):
        return RedirectResponse(url="/login", status_code=303)
    holder = request.session.get("user")
    cursor.execute("SELECT balance FROM accounts WHERE account_holder = %s", (holder,))
    account = cursor.fetchone()
    if account and amount > 0:
        if account[0] >= amount:
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_holder = %s", (amount, holder))
            conn.commit()
            return RedirectResponse(url="/customer_dashboard?msg=Withdrawal%20Successful", status_code=303)
        else:
            return RedirectResponse(url="/customer_dashboard?error=Insufficient%20Funds", status_code=303)
    return RedirectResponse(url="/customer_dashboard?error=Invalid%20Amount", status_code=303)


# =========================
# ADMIN ROUTES (CRUD)
# =========================

@app.get("/")
def home(request: Request):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    cursor.execute("SELECT * FROM accounts")
    accounts = cursor.fetchall()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"view": "admin_dashboard", "accounts": accounts}
    )

@app.get("/create")
def get_create(request: Request):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    return templates.TemplateResponse(request=request, name="index.html", context={"view": "create"})

@app.post("/add")
def add_account(request: Request, holder: str = Form(...), pin: str = Form(...), balance: float = Form(...)):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    sql = "INSERT INTO accounts (account_holder, pin, balance) VALUES (%s, %s, %s)"
    cursor.execute(sql, (holder, pin, balance))
    conn.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/update/{holder}")
def get_update(request: Request, holder: str):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    cursor.execute("SELECT * FROM accounts WHERE account_holder = %s", (holder,))
    account = cursor.fetchone()
    if not account:
        return RedirectResponse(url="/", status_code=303)
        
    return templates.TemplateResponse(request=request, name="index.html", context={"view": "update", "account": account})

@app.post("/update/{holder}")
def update_account(request: Request, holder: str, pin: str = Form(...), balance: float = Form(...)):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    sql = "UPDATE accounts SET pin = %s, balance = %s WHERE account_holder = %s"
    cursor.execute(sql, (pin, balance, holder))
    conn.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete_confirm/{holder}")
def delete_confirm(request: Request, holder: str):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    cursor.execute("SELECT * FROM accounts WHERE account_holder = %s", (holder,))
    account = cursor.fetchone()
    if not account:
        return RedirectResponse(url="/", status_code=303)
        
    return templates.TemplateResponse(request=request, name="index.html", context={"view": "delete", "account": account})

@app.post("/delete/{holder}")
def delete_account(request: Request, holder: str):
    if not get_current_admin(request):
        return RedirectResponse(url="/login", status_code=303)
        
    sql = "DELETE FROM accounts WHERE account_holder = %s"
    cursor.execute(sql, (holder,))
    conn.commit()
    return RedirectResponse(url="/", status_code=303)