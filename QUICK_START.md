# Quick Start Guide

## Initial Setup (For First-Time Users)

This guide will help you set up and run the Crop Recommendation System on both **Mac** and **Windows** after downloading the project as a zip file from GitHub.

---

## Prerequisites

Before you begin, ensure you have the following installed:

### For Mac:
- **Python 3.10 or higher** (check with `python3 --version`)
- **pip** (usually comes with Python)
- **Git** (optional, for cloning)

### For Windows:
- **Python 3.10 or higher** (download from [python.org](https://www.python.org/downloads/))
  - ⚠️ **Important**: During installation, check "Add Python to PATH"
- **pip** (usually comes with Python)
- **Git** (optional, for cloning)

---

## Step-by-Step Setup Instructions

### Step 1: Extract the Project

#### Mac:
1. Download the zip file from GitHub
2. Double-click to extract, or use:
   ```bash
   unzip CropRecommendation-main.zip
   ```
3. Navigate to the project directory:
   ```bash
   cd CropRecommendation-main
   # or if extracted to a different name:
   cd CropRecommendation
   ```

#### Windows:
1. Download the zip file from GitHub
2. Right-click the zip file → "Extract All..."
3. Open Command Prompt or PowerShell
4. Navigate to the project directory:
   ```cmd
   cd Downloads\CropRecommendation-main
   # or wherever you extracted it
   ```

---

### Step 2: Create Virtual Environment

A virtual environment isolates your project dependencies from other Python projects.

#### Mac:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

After activation, you should see `(venv)` at the beginning of your terminal prompt.

#### Windows (Command Prompt):
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

#### Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate.ps1
```

**Note for Windows PowerShell**: If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

After activation, you should see `(venv)` at the beginning of your prompt.

---

### Step 3: Install Dependencies

**Both Mac and Windows** (after activating virtual environment):

```bash
# Upgrade pip (recommended)
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This may take a few minutes as it installs Django, TensorFlow, and other dependencies.

---

### Step 4: Set Up Database

**Both Mac and Windows** (after activating virtual environment):

```bash
# Run database migrations
python manage.py migrate
```

This creates the SQLite database file (`db.sqlite3`) and sets up all necessary tables.

---

### Step 5: Create Admin User (Optional but Recommended)

**Both Mac and Windows** (after activating virtual environment):

```bash
# Create a superuser account for admin access
python manage.py createsuperuser
```

Follow the prompts to enter:
- Username
- Email (optional)
- Password (will be hidden as you type)

---

### Step 6: Collect Static Files

**Both Mac and Windows** (after activating virtual environment):

```bash
# Collect static files (CSS, JS, images)
python manage.py collectstatic
```

When prompted, type `yes` to confirm.

---

### Step 7: Run the Development Server

**Both Mac and Windows** (after activating virtual environment):

```bash
# Start the development server
python manage.py runserver
```

You should see output like:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

---

## Accessing the Application

Once the server is running, open your web browser and visit:

- **Home Page**: http://127.0.0.1:8000/
- **Landing Page**: http://127.0.0.1:8000/landing/
- **Dashboard**: http://127.0.0.1:8000/dashboard/ (requires login)
- **Login**: http://127.0.0.1:8000/login/
- **Register**: http://127.0.0.1:8000/register/
- **Admin Panel**: http://127.0.0.1:8000/admin/ (use superuser credentials)

---

## Quick Reference Commands

### Activate Virtual Environment

**Mac:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

### Deactivate Virtual Environment

**Both Mac and Windows:**
```bash
deactivate
```

### Run Server

**Both Mac and Windows** (after activating venv):
```bash
python manage.py runserver
```

### Run Server on Different Port

If port 8000 is already in use:
```bash
python manage.py runserver 8001
```

### Run Migrations

**Both Mac and Windows** (after activating venv):
```bash
python manage.py migrate
```

### Create Superuser

**Both Mac and Windows** (after activating venv):
```bash
python manage.py createsuperuser
```

### Collect Static Files

**Both Mac and Windows** (after activating venv):
```bash
python manage.py collectstatic
```

### Check for Errors

**Both Mac and Windows** (after activating venv):
```bash
python manage.py check
```

---

## Troubleshooting

### Issue: `python` command not found

**Mac:**
- Use `python3` instead of `python`
- Or ensure virtual environment is activated: `source venv/bin/activate`

**Windows:**
- Make sure Python was added to PATH during installation
- Try `py` instead of `python`
- Reinstall Python and check "Add Python to PATH"

### Issue: Virtual environment not found

**Both Mac and Windows:**
```bash
# Create it first
python3 -m venv venv  # Mac
python -m venv venv   # Windows

# Then activate and install dependencies
source venv/bin/activate  # Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Issue: Port 8000 is already in use

**Both Mac and Windows:**
```bash
# Use a different port
python manage.py runserver 8001
```

### Issue: `pip install` fails or is slow

**Both Mac and Windows:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing with timeout
pip install --default-timeout=100 -r requirements.txt

# Or use a different index
pip install -r requirements.txt -i https://pypi.org/simple
```

### Issue: ModuleNotFoundError after installation

**Both Mac and Windows:**
- Make sure virtual environment is activated (you should see `(venv)` in your prompt)
- Reinstall dependencies: `pip install -r requirements.txt`

### Issue: Database errors

**Both Mac and Windows:**
```bash
# Delete existing database (if any)
# Mac/Linux:
rm db.sqlite3

# Windows:
del db.sqlite3

# Then run migrations again
python manage.py migrate
```

### Issue: Static files not loading

**Both Mac and Windows:**
```bash
# Collect static files again
python manage.py collectstatic --noinput
```

### Issue: Windows PowerShell execution policy error

**Windows PowerShell only:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating the virtual environment again.

---

## Next Steps

1. **Explore the Application**: Visit http://127.0.0.1:8000/ and create an account
2. **Access Admin Panel**: Use your superuser credentials at http://127.0.0.1:8000/admin/
3. **Read Documentation**: Check `README.md` for more information about the project
4. **Check ML Models**: Ensure ML model files exist in `ml_training/models/` (they may need to be trained first)

---

## Important Notes

- **Always activate the virtual environment** before running any Django commands
- The database (`db.sqlite3`) is created automatically after running migrations
- Static files are collected to the `staticfiles/` directory
- The development server runs on `http://127.0.0.1:8000/` by default
- To stop the server, press `Ctrl+C` (Mac/Windows) in the terminal

---

## Getting Help

If you encounter issues not covered here:
1. Check the `README.md` file for more details
2. Review Django logs in `logs/django.log` (if available)
3. Run `python manage.py check` to identify configuration issues
4. Ensure all prerequisites are installed correctly
