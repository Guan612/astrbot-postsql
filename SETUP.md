# Setup Instructions

## Prerequisites

- Python 3.10 or higher

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:

   **Windows:**
   ```bash
   .venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Known Limitations

### MSYS2/MinGW64 Python Environment

If you are using MSYS2/MinGW64 Python on Windows, you may encounter build errors when installing `asyncpg`. This is because asyncpg requires compilation and precompiled wheels are not available for MSYS2/MinGW64 builds.

**Error Example:**
```
ERROR: Failed building wheel for asyncpg
```

**Solution:** Use a standard Windows Python installation (from python.org or Microsoft Store) instead of MSYS2/MinGW64 Python. The standard Windows Python provides precompiled wheels for asyncpg that will install without compilation.

### Alternative for MSYS2/MinGW64 Users

If you must use MSYS2/MinGW64 Python, you will need to:
1. Install PostgreSQL development headers
2. Install C build tools (gcc, make, etc.)
3. Install Cython
4. Build asyncpg from source

This is not recommended for most users.
