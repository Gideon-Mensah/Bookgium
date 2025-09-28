#!/bin/bash

# Fix all user URL namespacing issues in templates

echo "🔧 Fixing URL namespacing in templates..."

# Find all template files and replace non-namespaced user URLs
find templates/ -name "*.html" -type f -exec sed -i '' \
    -e "s/{% url 'user_create'/{% url 'users:user_create'/g" \
    -e "s/{% url 'user_list'/{% url 'users:user_list'/g" \
    -e "s/{% url 'user_detail'/{% url 'users:user_detail'/g" \
    -e "s/{% url 'user_edit'/{% url 'users:user_edit'/g" \
    -e "s/{% url 'user_delete'/{% url 'users:user_delete'/g" \
    -e "s/{% url 'toggle_user_status'/{% url 'users:toggle_user_status'/g" \
    -e "s/{% url 'dashboard'/{% url 'users:dashboard'/g" \
    -e "s/{% url 'profile'/{% url 'users:profile'/g" \
    -e "s/{% url 'currency_preference'/{% url 'users:currency_preference'/g" \
    -e "s/{% url 'password_reset_done'/{% url 'users:password_reset_done'/g" \
    -e "s/{% url 'password_reset_complete'/{% url 'users:password_reset_complete'/g" \
    -e "s/{% url 'password_change_done'/{% url 'users:password_change_done'/g" \
    -e "s/{% url 'logout'/{% url 'users:logout'/g" \
    {} \;

echo "✅ URL namespacing fixed in all templates!"
