import os, sys
sys.path.append(r"f:\Vash Studios\FuseHealth\Limitless_marketing_dashboard")
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client

c = Client()
c.login(username="founder", password="Test1234!")
res = c.post("/api/projects/premierstaff/invite", {"email": "newuser_test@example.com", "role": "Admin"}, content_type="application/json")
print("Status:", res.status_code)
print("Content:", res.content)
