#!/bin/bash
# Fix database configuration: Ensure PostgreSQL consistency

echo "=== DATABASE CONFIGURATION FIX ==="

echo "Step 1: Remove SQLite database (causes confusion)..."
if [ -f "db.sqlite3" ]; then
    mv db.sqlite3 db.sqlite3.backup
    echo "✓ Moved db.sqlite3 to db.sqlite3.backup"
else
    echo "✓ No SQLite database found"
fi

echo "Step 2: Check PostgreSQL availability..."
if command -v psql &> /dev/null; then
    echo "✓ PostgreSQL client (psql) is available"
else
    echo "❌ PostgreSQL client not found. Install PostgreSQL:"
    echo "   macOS: brew install postgresql"
    echo "   Ubuntu: sudo apt-get install postgresql"
fi

echo "Step 3: Test PostgreSQL connection..."
export DATABASE_URL="postgres://postgres:password@localhost:5432/bookgium_db"

# Try to connect to PostgreSQL
if psql "$DATABASE_URL" -c "SELECT 1;" &> /dev/null; then
    echo "✓ PostgreSQL connection successful"
else
    echo "❌ PostgreSQL connection failed"
    echo "   Make sure PostgreSQL is running:"
    echo "   macOS: brew services start postgresql"
    echo "   Ubuntu: sudo systemctl start postgresql"
    echo ""
    echo "   Create the database:"
    echo "   createdb bookgium_db"
fi

echo "Step 4: Environment configuration..."
if [ -f ".env" ]; then
    echo "✓ .env file exists"
else
    echo "Creating .env file for local development..."
    cat > .env << EOF
DEBUG=True
DATABASE_URL=postgres://postgres:password@localhost:5432/bookgium_db
SECRET_KEY=django-insecure-local-development-key
EOF
    echo "✓ Created .env file"
fi

echo ""
echo "=== DATABASE FIX COMPLETED ==="
echo "✅ Removed SQLite confusion"  
echo "✅ Configured for PostgreSQL consistency"
echo ""
echo "Next steps:"
echo "1. Start PostgreSQL: brew services start postgresql"
echo "2. Create database: createdb bookgium_db"
echo "3. Test migrations: python manage.py fresh_setup --confirm-reset"
