"""
Configuration module for Industrial AI - Quotation Intelligence.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o"  # Change to gpt-5.5 when available

# Application Configuration
APP_TITLE = "Industrial AI - Quotation Intelligence"
APP_SUBTITLE = "AI Powered Motor Rewinding Quotation Generator"
APP_VERSION = "1.0.0"

# Company Details
COMPANY_NAME = "Industrial AI - Quotation Intelligence"
COMPANY_ADDRESS = "Industrial Area, Phase II, Pune, Maharashtra 411026"
COMPANY_PHONE = "+91 20 2712 3456"
COMPANY_EMAIL = "info@industrialai-qi.com"
COMPANY_WEBSITE = "www.industrialai-qi.com"

# File Upload Configuration
UPLOAD_DIR = "uploads"
QUOTATION_DIR = "quotations"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Database
DATABASE_URL = "sqlite:///./inventory.db"

# Quotation Settings
QUOTATION_VALIDITY_DAYS = 30
GST_RATE = 18.0

# Supported Manufacturers
SUPPORTED_MANUFACTURERS = [
    "Kirloskar",
    "ABB",
    "Siemens",
    "CG",
    "Bharat Bijlee",
    "WEG",
    "Crompton",
]
