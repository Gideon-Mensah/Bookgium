from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class Client(models.Model):
    """Model representing a client/customer"""
    COMPANY_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('corporation', 'Corporation'),
        ('nonprofit', 'Non-Profit'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('prospective', 'Prospective'),
        ('former', 'Former'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, help_text="Client or company name")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Company Information
    company_type = models.CharField(
        max_length=20, 
        choices=COMPANY_TYPE_CHOICES, 
        default='business'
    )
    registration_number = models.CharField(max_length=50, blank=True)
    tax_id = models.CharField(max_length=50, blank=True, help_text="Tax ID or VAT number")
    
    # Contact Information
    contact_person = models.CharField(max_length=200, blank=True)
    contact_title = models.CharField(max_length=100, blank=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    payment_terms = models.CharField(max_length=100, blank=True, help_text="e.g., Net 30 days")
    
    # Notes and Tracking
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('clients:detail', kwargs={'pk': self.pk})
    
    def get_full_address(self):
        """Return the full address as a string"""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def display_contact(self):
        """Return formatted contact information"""
        if self.contact_person and self.contact_title:
            return f"{self.contact_person} ({self.contact_title})"
        elif self.contact_person:
            return self.contact_person
        else:
            return "No contact person"

class ClientNote(models.Model):
    """Model for tracking notes and interactions with clients"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.client.name}"