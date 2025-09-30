#!/bin/bash
# Drop migration folders and regenerate them

echo "=== DROPPING AND REGENERATING MIGRATIONS ==="

# List of your Django apps
APPS="users accounts invoices reports dashboard settings clients payroll audit help_chat"

echo "Step 1: Backing up existing migrations..."
mkdir -p migration_backup/$(date +%Y%m%d_%H%M%S)
for app in $APPS; do
    if [ -d "$app/migrations" ]; then
        echo "  Backing up $app/migrations..."
        cp -r "$app/migrations" "migration_backup/$(date +%Y%m%d_%H%M%S)/$app_migrations" 2>/dev/null || true
    fi
done

echo "Step 2: Deleting migration files (keeping __init__.py)..."
for app in $APPS; do
    if [ -d "$app/migrations" ]; then
        echo "  Cleaning $app/migrations/..."
        
        # Remove numbered migration files
        rm -f "$app/migrations"/[0-9]*.py
        
        # Remove __pycache__
        rm -rf "$app/migrations/__pycache__"
        
        # Ensure __init__.py exists
        touch "$app/migrations/__init__.py"
        
        echo "    ✓ Cleaned $app/migrations/"
    else
        echo "    ⚠ $app/migrations/ not found"
    fi
done

echo "Step 3: Regenerating migrations..."
python manage.py makemigrations

echo "Step 4: Listing new migration files..."
for app in $APPS; do
    if [ -d "$app/migrations" ]; then
        migration_files=$(ls "$app/migrations"/[0-9]*.py 2>/dev/null | wc -l)
        if [ "$migration_files" -gt 0 ]; then
            echo "  📂 $app/migrations/:"
            ls "$app/migrations"/[0-9]*.py 2>/dev/null | while read file; do
                echo "    📄 $(basename "$file")"
            done
        else
            echo "  📂 $app/migrations/: No migrations needed"
        fi
    fi
done

echo ""
echo "=== MIGRATION REGENERATION COMPLETED! ==="
echo "✓ All migration files have been regenerated"
echo "ℹ️  Backup saved in: migration_backup/$(date +%Y%m%d_%H%M%S)/"
echo ""
echo "Next steps:"
echo "1. Test locally: python manage.py migrate"
echo "2. Or use fresh_setup: python manage.py fresh_setup --confirm-reset"
