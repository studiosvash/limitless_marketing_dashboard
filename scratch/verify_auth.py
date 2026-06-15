from django.test import Client
from django.contrib.auth.models import User

# 1. Anonymous hitting a protected page -> redirected to login
c = Client()
r = c.get("/", HTTP_HOST="localhost")
print("anon GET / ->", r.status_code, "redirect:", r.headers.get("Location"))

# 2. Login page is public
print("GET /login/ ->", c.get("/login/", HTTP_HOST="localhost").status_code)

# 3. Login as ads; overview is allowed for all roles
ok = c.login(username="ads", password="changeme-ads")
print("ads login ok:", ok)
print("ads GET / (overview) ->", c.get("/", HTTP_HOST="localhost").status_code)

# 4. Role matrix via can_access
for uname in ["founder", "seo", "ads"]:
    p = User.objects.get(username=uname).profile
    print(f"{uname:<8} role={p.role:<8} overview={p.can_access('overview')} "
          f"seo={p.can_access('seo')} ads={p.can_access('ads')}")
