# Audit Logging System for Bookgium

## Overview

A comprehensive audit logging system has been added to the Bookgium Django accounting application. This system tracks all important changes to models, user sessions, and provides detailed reporting capabilities.

## Features

### 1. **Comprehensive Model Auditing**
- Tracks CREATE, UPDATE, DELETE operations on important models
- Records field-level changes with before/after values
- Supports all major accounting models (Accounts, Journal Entries, Transactions, Users)

### 2. **User Session Tracking**
- Monitors user login/logout activities
- Tracks IP addresses, user agents, and session durations
- Maintains active session status

### 3. **Audit Dashboard & Reports**
- Interactive dashboard with activity charts
- Filterable audit log listings
- Detailed audit log views with change history
- User session management views

### 4. **Configurable Settings**
- Enable/disable auditing for specific models
- Configure retention policies
- Control which actions to audit (create/update/delete/view/login)
- Email notifications for critical changes

## Implementation Details

### Models Created

1. **AuditLog**: Main audit trail table
   - Tracks user, action, object, changes, IP address, timestamp
   - Uses Django's ContentType framework for flexible object tracking
   - Stores changes as JSON for detailed field-level tracking

2. **UserSession**: User session tracking
   - Login/logout times, IP addresses, user agents
   - Session duration calculations
   - Active session status

3. **AuditSettings**: Configuration management
   - Model-specific audit settings
   - Action-specific settings
   - Retention and notification settings

### Components Added

#### Backend Components:
- `audit/models.py` - Core audit models
- `audit/signals.py` - Django signal handlers for automatic auditing
- `audit/middleware.py` - Request context middleware
- `audit/views.py` - Audit dashboard and reporting views
- `audit/admin.py` - Django admin integration
- `audit/utils.py` - Utility functions for IP detection and change tracking

#### Frontend Components:
- `templates/audit/audit_dashboard.html` - Main dashboard with charts
- `templates/audit/audit_log_list.html` - Filterable audit log listing
- `templates/audit/audit_log_detail.html` - Detailed audit log view
- `templates/audit/user_session_list.html` - User session tracking

#### Management Commands:
- `init_audit_settings` - Initialize default audit settings
- `cleanup_audit_logs` - Clean up old audit logs based on retention policy
- `demo_audit` - Demonstrate audit functionality

### URLs Added
- `/audit/` - Audit dashboard
- `/audit/logs/` - Audit log listing
- `/audit/logs/<id>/` - Detailed audit log view
- `/audit/sessions/` - User session listing
- `/audit/api/chart-data/` - API endpoint for dashboard charts

## Configuration

### Settings Updated
```python
# In bookgium/settings.py
INSTALLED_APPS = [
    # ... existing apps ...
    'audit',
]

MIDDLEWARE = [
    # ... existing middleware ...
    'audit.middleware.AuditMiddleware',  # Added for audit logging
]
```

### Access Control
- Audit views are restricted to admin users and staff
- Uses `UserPassesTestMixin` to ensure proper authorization
- Admin users can access all audit functionality

## Usage

### 1. **Access Audit Dashboard**
- Navigate to `/audit/` (available in sidebar for admin users)
- View activity statistics, recent logs, and charts
- Monitor system usage patterns

### 2. **View Audit Logs**
- Filter by user, action, model, date range, or search terms
- Click on individual logs to see detailed change information
- Export or print audit reports

### 3. **Monitor User Sessions**
- Track active and inactive user sessions
- View login/logout patterns
- Monitor session durations and IP addresses

### 4. **Configure Audit Settings**
- Access via Django admin panel
- Enable/disable auditing for specific models
- Set retention policies and notification preferences

## Security Features

### 1. **Change Tracking**
- Immutable audit logs (read-only after creation)
- Field-level change detection with before/after values
- Tamper-evident logging with timestamps and user tracking

### 2. **Session Security**
- Comprehensive session tracking
- IP address and user agent logging
- Automatic session cleanup on logout

### 3. **Access Control**
- Role-based access to audit functionality
- Admin-only access to sensitive audit information
- Secure API endpoints for dashboard data

## Maintenance

### 1. **Log Cleanup**
```bash
# Clean up logs older than 365 days (default retention)
python manage.py cleanup_audit_logs

# Clean up logs older than 90 days
python manage.py cleanup_audit_logs --days 90

# Dry run to see what would be deleted
python manage.py cleanup_audit_logs --dry-run
```

### 2. **Settings Management**
```bash
# Initialize default audit settings
python manage.py init_audit_settings
```

### 3. **Performance Considerations**
- Audit logs are indexed for efficient querying
- Background cleanup commands for log retention
- Configurable auditing to reduce overhead when needed

## Integration with Existing System

### 1. **Seamless Integration**
- Uses Django signals for automatic auditing
- No changes required to existing model code
- Middleware handles request context automatically

### 2. **Backward Compatibility**
- Existing functionality remains unchanged
- Audit system can be disabled without affecting core features
- Optional components can be enabled/disabled as needed

### 3. **Scalability**
- Efficient database queries with proper indexing
- JSON storage for flexible change tracking
- Configurable retention policies to manage database size

## Testing

The audit system includes a demonstration command:
```bash
python manage.py demo_audit
```

This creates sample data and shows how the audit system tracks changes.

## Future Enhancements

1. **Email Notifications**: Automated alerts for critical changes
2. **Report Generation**: PDF/Excel export of audit reports
3. **Advanced Analytics**: Trend analysis and anomaly detection
4. **API Integration**: RESTful API for external audit tools
5. **Real-time Monitoring**: WebSocket integration for live audit feeds

---

The audit logging system provides comprehensive tracking and monitoring capabilities for the Bookgium accounting application, ensuring data integrity, security compliance, and detailed change history for all critical operations.
