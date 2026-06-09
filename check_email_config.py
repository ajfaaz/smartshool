#!/usr/bin/env python
"""
Email Configuration Test Script

This script tests if email is properly configured.
Run with: python manage.py shell < check_email_config.py
"""

from django.conf import settings
from django.core.mail import send_mail

print("\n" + "="*60)
print("EMAIL CONFIGURATION CHECK")
print("="*60)

print("\nEmail Settings:")
print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"  EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"  PASSWORD_RESET_TIMEOUT: {settings.PASSWORD_RESET_TIMEOUT} seconds")

if settings.EMAIL_HOST:
    print("\n✓ Email backend is configured for SMTP")
    print("  - Email will be sent via configured SMTP server")
else:
    print("\n⚠ Email backend is configured for console output")
    print("  - Emails will be printed to console (development mode)")
    print("  - To enable SMTP, set EMAIL_HOST environment variable")

print("\n" + "="*60)
print("Configuration Notes:")
print("="*60)
print("""
For Production Email Setup:
  1. Set EMAIL_HOST (e.g., smtp.gmail.com, smtp.sendgrid.net)
  2. Set EMAIL_HOST_USER (your email/username)
  3. Set EMAIL_HOST_PASSWORD (your password/API key)
  4. Set DEFAULT_FROM_EMAIL (sender email address)
  5. Adjust EMAIL_PORT (usually 587 for TLS, 465 for SSL)

For Gmail:
  - EMAIL_HOST: smtp.gmail.com
  - EMAIL_PORT: 587
  - EMAIL_USE_TLS: True
  - EMAIL_USE_SSL: False
  - Use "App Password" not regular password

For Development:
  - Leave EMAIL_HOST empty to use console backend
  - Emails appear in terminal/logs for testing
""")
print("="*60)
