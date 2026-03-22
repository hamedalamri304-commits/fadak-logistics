# 🚀 دليل النشر — فدك اللوجستية

## الطريقة الأسهل: Railway.app (مجاني)

### الخطوة 1: GitHub
1. اذهب إلى github.com وأنشئ حساباً
2. اضغط "New repository" → اسمه: fadak-logistics
3. اجعله Private
4. اضغط "uploading an existing file"
5. ارفع جميع الملفات (ما عدا fadak.db)

### الخطوة 2: Railway
1. اذهب إلى railway.app
2. اضغط "Start a New Project"
3. اختر "Deploy from GitHub repo"
4. اختر fadak-logistics
5. انتظر 2-3 دقائق حتى يكتمل النشر

### الخطوة 3: إضافة PostgreSQL
1. في Railway dashboard → "New Service" → "Database" → "PostgreSQL"
2. ستجد DATABASE_URL في قسم Variables
3. Railway يضيفها تلقائياً للتطبيق

### الخطوة 4: متغيرات البيئة (مهم للأمان)
في Railway → Variables → أضف:
- SECRET_KEY = أي نص عشوائي طويل
- ADMIN_PASS = كلمة مرور admin الجديدة
- MANAGER_PASS = كلمة مرور manager الجديدة

### الخطوة 5: الدومين
Railway → Settings → Generate Domain
ستحصل على: fadak-logistics.up.railway.app

---
## بيانات الدخول الافتراضية
- admin / fadak2026
- manager / manager123

⚠️ غيّر كلمات المرور عبر متغيرات البيئة قبل الرفع!
