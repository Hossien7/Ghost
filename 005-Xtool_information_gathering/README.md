🔒 Security Toolkit - WHOIS, DNS Enum & HTTP Header Analyzer
https://img.shields.io/badge/python-3.8%252B-blue
https://img.shields.io/badge/license-MIT-green
https://img.shields.io/github/stars/yourusername/security-toolkit?style=social

یک ابزار امنیتی پایتونی حرفه‌ای برای تحلیل دامنه‌ها و بررسی آسیب‌پذیری‌های اولیه سرویس‌های وب. این ابزار به صورت خط فرمانی (CLI) طراحی شده و از کتابخانه rich برای نمایش زیبای نتایج استفاده می‌کند.

✨ ویژگی‌های کلیدی
WHOIS Lookup: استخراج اطلاعات ثبت دامنه (ثبت‌کننده، تاریخ ایجاد، تاریخ انقضا)

DNS Enumeration: بررسی رکوردهای DNS شامل A, MX, TXT, NS, CNAME

HTTP Header Analyzer: تحلیل هدرهای HTTP برای کشف اطلاعات حساس

رابط کاربری زیبا: نمایش نتایج در جداول رنگی و خوانا

پیکربندی آسان: اجرا با یک دستور ساده

🚀 نصب و راه‌اندازی
پیش‌نیازها
پایتون 3.8 یا بالاتر

pip (مدیریت بسته‌های پایتون)

نصب کتابخانه‌های مورد نیاز
bash
# Clone the repository
git clone https://github.com/yourusername/security-toolkit.git
cd security-toolkit

# Install dependencies
pip install -r requirements.txt
کتابخانه‌های مورد استفاده
کتابخانه	نسخه	توضیحات
python-whois	آخرین نسخه	استخراج اطلاعات WHOIS
dnspython	2.3.0	حل‌کننده رکوردهای DNS
requests	2.28.2	ارسال درخواست‌های HTTP
rich	13.4.2	نمایش زیبای نتایج در ترمینال
🛠 روش استفاده
دستورات اصلی:
bash
python security_tool.py [OPTIONS] [TARGET]
گزینه‌ها:
پرچم	توضیح	مثال
-w یا --whois	استخراج اطلاعات WHOIS	python security_tool.py -w example.com
-d یا --dns	استخراج رکوردهای DNS	python security_tool.py -d example.com
-http یا --http	تحلیل هدرهای HTTP	python security_tool.py -http example.com
-a یا --all	اجرای تمام بررسی‌ها	python security_tool.py -a example.com
مثال کامل:
bash
# بررسی کامل یک دامنه

# خروجی نمونه:

📊 نمونه خروجی‌ها
1. اطلاعات WHOIS

2. رکوردهای DNS

3. هدرهای HTTP

🧠 موارد استفاده
بررسی امنیتی اولیه وبسایت‌ها

شناسایی اطلاعات سرور و فناوری‌های backend

بررسی پیکربندی DNS

کنترل تاریخ انقضای دامنه

شناسایی هدرهای امنیتی گم‌شده

جمع‌آوری اطلاعات برای تست نفوذ

⚠️ محدودیت‌ها و هشدارها
برخی دامنه‌ها ممکن است اطلاعات WHOIS را محدود کرده باشند

سرورها ممکن است درخواست‌های مکرر را مسدود کنند

برای تحلیل SSL/TLS نیاز به توسعه بیشتر دارد

نتایج DNS ممکن است تحت تأثیر تنظیمات محلی باشد

❗ این ابزار فقط برای اهداف آموزشی و تست قانونی طراحی شده است. هرگونه استفاده غیرمجاز ممنوع است.

🤝 مشارکت در توسعه
پروژه را بهبود ببخشید! مراحل مشارکت:

پروژه را Fork کنید

Branch جدید ایجاد کنید:
git checkout -b feature/new-feature

تغییرات را Commit کنید:
git commit -m 'Add some feature'

تغییرات را Push کنید:
git push origin feature/new-feature

یک Pull Request باز کنید

ویژگی‌های پیشنهادی برای توسعه:
افزودن اسکنر SSL/TLS

پیاده‌سازی بررسی زیردامنه‌ها

افزودن قابلیت ذخیره‌سازی نتایج در فایل

پشتیبانی از اسکن دسته‌ای دامنه‌ها

📜 مجوز
این پروژه تحت مجوز MIT منتشر شده است - برای جزئیات به فایل LICENSE مراجعه کنید.

text
MIT License
Copyright (c) 2023 [Hossein Tajary]
✉️ تماس با من
برای سوالات و پیشنهادات می‌توانید با من در تماس باشید:
    hossien.tajary@gmail.com
text

## 🎁 نکات نصب برای نمایش بهتر

1. برای بهترین تجربه نمایش، از ترمینال‌های مدرن استفاده کنید:
   - Windows: [Windows Terminal](https://aka.ms/terminal)
   - macOS: [iTerm2](https://iterm2.com/)
   - Linux: [GNOME Terminal](https://help.gnome.org/users/gnome-terminal/)

2. اگر با خطای فونت مواجه شدید، فونت‌های دارای قابلیت‌های Unicode نصب کنید:
   - [Fira Code](https://github.com/tonsky/FiraCode)
   - [Cascadia Code](https://github.com/microsoft/cascadia-code)

3. برای اجرای سریع‌تر ابزار، از محیط‌های مجازی پایتون استفاده کنید:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate    # Windows
pip install -r requirements.txt
🌟 ستاره‌ها و حمایت
اگر این پروژه برای شما مفید بود، لطفاً با دادن ستاره (⭐) از آن حمایت کنید!
