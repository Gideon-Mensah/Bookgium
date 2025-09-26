from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Admin'),
        ('accountant', 'Accountant'),
        ('hr', 'HR'),
        ('viewer', 'Viewer'),
    ])
    
    # Currency preference for this user
    preferred_currency = models.CharField(
        max_length=3, 
        default='USD',
        choices=[
            ('USD', 'US Dollar ($)'),
            ('EUR', 'Euro (€)'),
            ('GBP', 'British Pound (£)'),
            ('CAD', 'Canadian Dollar (C$)'),
            ('AUD', 'Australian Dollar (A$)'),
            ('JPY', 'Japanese Yen (¥)'),
            ('CHF', 'Swiss Franc (CHF)'),
            ('CNY', 'Chinese Yuan (¥)'),
            ('INR', 'Indian Rupee (₹)'),
            ('BRL', 'Brazilian Real (R$)'),
            ('ZAR', 'South African Rand (R)'),
            ('MXN', 'Mexican Peso ($)'),
            ('SGD', 'Singapore Dollar (S$)'),
            ('HKD', 'Hong Kong Dollar (HK$)'),
            ('NZD', 'New Zealand Dollar (NZ$)'),
        ]
    )
