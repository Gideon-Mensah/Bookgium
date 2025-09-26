from django.db import models

# Create your models here.
class CompanySettings(models.Model):
    # Organization Information
    organization_name = models.CharField(max_length=200, default="Your Organization Name", 
                                       help_text="Name of your organization/company")
    organization_address = models.TextField(blank=True, null=True, 
                                          help_text="Organization address")
    organization_phone = models.CharField(max_length=50, blank=True, null=True)
    organization_email = models.EmailField(blank=True, null=True)
    organization_website = models.URLField(blank=True, null=True)
    organization_logo = models.ImageField(upload_to='organization/', blank=True, null=True,
                                        help_text="Organization logo for reports")
    
    # Financial Settings
    fiscal_year_start = models.DateField()
    currency = models.CharField(max_length=10)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return self.organization_name
    
    class Meta:
        verbose_name = "Company Settings"
        verbose_name_plural = "Company Settings"

