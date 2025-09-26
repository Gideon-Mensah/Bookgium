# 🏢 Multi-Tenant Bookgium - Complete Setup Guide

## 🎯 Overview

Your Django Bookgium application has been configured for **true multi-tenancy** using `django-tenants`. Each client organization gets:

- **Complete data isolation** (separate database schemas)
- **Custom domains** (e.g., `client1.bookgium.com`, `client2.bookgium.com`)
- **Individual branding** (logos, colors, currency preferences)
- **Separate user bases** (users belong to specific tenants)
- **Independent configurations** (chart of accounts, settings, etc.)

---

## 📁 Multi-Tenant Architecture

### Schema Structure:
- **`public` schema**: Stores tenant/client information, shared data
- **Tenant schemas**: Each client gets their own schema (e.g., `client1`, `client2`)

### Data Separation:
- **Shared Apps**: `clients` (tenant management)
- **Tenant Apps**: `users`, `accounts`, `invoices`, `payroll`, etc.

---

## 🛠️ Updated Files for Multi-Tenancy

### 1. **Core Configuration:**
- ✅ `clients/models.py` - Updated with `TenantMixin` and `DomainMixin`
- ✅ `bookgium/settings.py` - Multi-tenant configuration
- ✅ `bookgium/production_settings.py` - Production multi-tenant settings
- ✅ `bookgium/urls.py` - Schema-aware URL routing
- ✅ `requirements.txt` - Added `redis` for caching

### 2. **Management Commands:**
- ✅ `clients/management/commands/create_tenant.py` - Create new tenants
- ✅ `clients/management/commands/list_tenants.py` - List all tenants
- ✅ `clients/management/commands/create_tenant_superuser.py` - Create admin users

### 3. **Middleware & Context:**
- ✅ `clients/middleware.py` - Custom tenant resolution
- ✅ `clients/context_processors.py` - Tenant context for templates

---

## 🚀 Local Development Setup

### Step 1: Install PostgreSQL
```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb bookgium_db
```

### Step 2: Update Environment
```bash
# Install new dependencies
pip install -r requirements.txt

# Run migrations for shared apps
python manage.py migrate_schemas --shared

# Run migrations for tenant apps (this creates the public schema)
python manage.py migrate_schemas
```

### Step 3: Create Your First Tenant
```bash
# Create a tenant with domain
python manage.py create_tenant "Demo Company" demo.localhost

# Create superuser for the tenant
python manage.py create_tenant_superuser demo_company --username admin --email admin@demo.com
```

### Step 4: Update Hosts File (for local testing)
```bash
# Add to /etc/hosts
127.0.0.1 demo.localhost
127.0.0.1 client1.localhost  
127.0.0.1 client2.localhost
```

### Step 5: Test Multi-Tenancy
```bash
# Start development server
python manage.py runserver

# Access different tenants:
# http://demo.localhost:8000 (tenant-specific app)
# http://localhost:8000 (public schema - tenant management)
```

---

## 🌐 Production Deployment on Render

### Step 1: Environment Variables
Add these to your Render environment variables:

```bash
# Multi-tenant specific
TENANT_MODEL=clients.Client
TENANT_DOMAIN_MODEL=clients.Domain

# Database (PostgreSQL required)
DATABASE_URL=postgresql://user:password@host:port/database

# Domain configuration
ALLOWED_HOSTS=.onrender.com,.bookgium.com,localhost
```

### Step 2: Deployment Process
```bash
# Your build script (build.sh) has been updated to handle multi-tenancy
./build.sh  # This will run schema migrations properly
```

### Step 3: Post-Deployment Setup
```bash
# In Render shell, create your first tenant
python manage.py create_tenant "Your First Client" yourfirstclient.onrender.com

# Create admin user for the tenant
python manage.py create_tenant_superuser yourfirstclient --username admin
```

---

## 🏗️ Multi-Tenant Management

### Creating New Tenants

**Command Line:**
```bash
python manage.py create_tenant "Client Name" client.domain.com --plan professional
```

**Programmatically:**
```python
from clients.models import Client, Domain

# Create tenant
tenant = Client.objects.create(
    name="New Client",
    schema_name="new_client",
    plan_type="professional"
)

# Create domain
Domain.objects.create(
    domain="newclient.bookgium.com",
    tenant=tenant,
    is_primary=True
)
```

### Managing Tenants

**List all tenants:**
```bash
python manage.py list_tenants --detailed
```

**Access tenant data:**
```python
from django_tenants.utils import schema_context
from clients.models import Client

tenant = Client.objects.get(schema_name='client1')
with schema_context('client1'):
    # All queries here are isolated to client1
    from django.contrib.auth import get_user_model
    User = get_user_model()
    users = User.objects.all()  # Only client1's users
```

---

## 🔧 Development Features

### Tenant-Aware Views
```python
from django.db import connection

def my_view(request):
    current_tenant = connection.tenant
    tenant_name = current_tenant.name
    tenant_currency = current_tenant.currency
    # ... rest of your view logic
```

### Template Context
Every template automatically has access to:
```html
<!-- Current tenant information -->
<h1>Welcome to {{ tenant_name }}</h1>
<p>Currency: {{ tenant_currency_symbol }}</p>
<p>Plan: {{ tenant_plan }}</p>

<!-- Conditional tenant features -->
{% if tenant_plan == 'enterprise' %}
    <!-- Enterprise-only features -->
{% endif %}
```

### Tenant-Specific Branding
```html
<!-- Use tenant colors and logo -->
<div style="color: {{ tenant_primary_color }}">
    {% if tenant_logo %}
        <img src="{{ tenant_logo.url }}" alt="{{ tenant_name }}">
    {% endif %}
</div>
```

---

## 📊 Domain Configuration

### Subdomain Pattern
- `client1.bookgium.com` → Schema: `client1`
- `client2.bookgium.com` → Schema: `client2`
- `demo.bookgium.com` → Schema: `demo`

### Custom Domains
- `accounting.clientcompany.com` → Schema: `clientcompany`
- `books.anotherclient.org` → Schema: `anotherclient`

### Domain Management
```python
# Add additional domains to existing tenant
tenant = Client.objects.get(name="Demo Company")
Domain.objects.create(
    domain="demo.customdomain.com",
    tenant=tenant,
    is_primary=False
)
```

---

## 🔐 Security & Isolation

### Complete Data Isolation
- ✅ **Database Level**: Each tenant has separate PostgreSQL schema
- ✅ **Application Level**: All queries automatically filtered by tenant
- ✅ **User Level**: Users cannot access other tenants' data
- ✅ **File Level**: Media files can be tenant-specific

### Security Best Practices
- ✅ Automatic tenant detection via domain
- ✅ No cross-tenant data leakage possible
- ✅ Tenant-specific admin interfaces
- ✅ Role-based access within tenants

---

## 🚦 Testing Multi-Tenancy

### Test Tenant Isolation
```python
# Create test data in different tenants
from django_tenants.utils import schema_context

# Data in tenant1
with schema_context('tenant1'):
    User.objects.create(username='user1')

# Data in tenant2  
with schema_context('tenant2'):
    User.objects.create(username='user2')

# Verify isolation
with schema_context('tenant1'):
    assert User.objects.count() == 1  # Only sees tenant1 data

with schema_context('tenant2'):
    assert User.objects.count() == 1  # Only sees tenant2 data
```

---

## 📈 Scaling Considerations

### Database Performance
- **Connection Pooling**: Configured for production
- **Schema Indexing**: Each tenant schema has independent indexes
- **Query Optimization**: Tenant-aware query optimization

### Application Scaling
- **Horizontal Scaling**: Each tenant can be on different servers
- **Load Balancing**: Domain-based routing
- **Caching**: Tenant-aware Redis caching

### Resource Management
- **Per-Tenant Limits**: Storage, users, features
- **Usage Monitoring**: Built-in usage tracking
- **Billing Integration**: Ready for subscription billing

---

## 🎉 Benefits of Multi-Tenancy

### For Your Business
- 🏢 **Single Codebase** - Manage all clients from one application
- 💰 **Scalable Revenue** - Easy to add new clients
- 🛡️ **Enterprise Security** - Complete data isolation
- 🎨 **White-Label Ready** - Custom branding per client

### For Your Clients
- 🔒 **Data Security** - Their data is completely isolated
- 🌐 **Custom Domains** - Professional appearance
- ⚙️ **Individual Settings** - Their own configurations
- 👥 **Team Management** - Their own user base

---

## 🆘 Troubleshooting

### Common Issues

**1. Tenant Not Found**
```bash
# Check domain configuration
python manage.py list_tenants --detailed
```

**2. Schema Errors**
```bash
# Run schema migrations
python manage.py migrate_schemas
```

**3. Domain Resolution**
```bash
# Verify domain points to correct tenant
python manage.py shell
>>> from clients.models import Domain
>>> Domain.objects.all()
```

**4. User Access Issues**
```bash
# Create tenant-specific superuser
python manage.py create_tenant_superuser schema_name
```

---

## 📚 Next Steps

1. **Deploy to Production** - Follow the updated deployment guide
2. **Create Client Onboarding** - Build UI for tenant creation
3. **Add Billing System** - Integrate subscription management
4. **Custom Domains** - Set up DNS management
5. **Advanced Features** - Per-tenant feature flags

---

**🎊 Congratulations!** 

Your Django Bookgium application is now a **professional multi-tenant SaaS platform**! Each client gets their own secure, isolated accounting system while you manage everything from a single codebase.

**Key Commands to Remember:**
```bash
# Create tenant
python manage.py create_tenant "Client Name" domain.com

# List tenants  
python manage.py list_tenants

# Create admin user
python manage.py create_tenant_superuser schema_name

# Run migrations
python manage.py migrate_schemas
```

Your application is now ready to serve multiple organizations simultaneously! 🚀
