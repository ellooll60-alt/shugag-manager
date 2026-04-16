import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date

# --- 1. إعداد قاعدة البيانات ---
conn = sqlite3.connect('comprehensive_rentals.db', check_same_thread=False)
c = conn.cursor()

# إنشاء الجداول الأساسية وجدول الإعدادات الجديد
c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS units_names (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS platforms (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS bookings 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, unit_no TEXT, client_name TEXT, 
              phone TEXT, platform TEXT, price REAL, check_in DATE, check_out DATE,
              expenses REAL, compensations REAL, note TEXT, bill_path TEXT, added_by TEXT)''')

# إضافة بيانات افتراضية
c.execute("INSERT OR IGNORE INTO users VALUES ('admin', '1234', 'مدير')")
c.execute("INSERT OR IGNORE INTO settings VALUES ('app_name', 'نظام إدارة الوحدات السكنية')")
conn.commit()

if not os.path.exists("all_bills"): os.makedirs("all_bills")
if not os.path.exists("brand"): os.makedirs("brand")

# دالة لجلب الإعدادات
def get_setting(key, default):
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    res = c.fetchone()
    return res[0] if res else default

# تهيئة الجلسة
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'selected_unit' not in st.session_state: st.session_state['selected_unit'] = None

# --- 2. عرض الهوية (الشعار والاسم) ---
app_name = get_setting('app_name', 'نظام إدارة الوحدات')
logo_path = get_setting('logo_path', '')

st.set_page_config(page_title=app_name, layout="wide")

# عرض الهوية في الأعلى
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=120)
with col_title:
    st.title(app_name)

# --- 3. نظام تسجيل الدخول ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 دخول النظام")
    u_input = st.sidebar.text_input("اسم المستخدم")
    p_input = st.sidebar.text_input("كلمة المرور", type="password")
    if st.sidebar.button("دخول"):
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (u_input, p_input))
        res = c.fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user_name': u_input, 'user_role': res[0]})
            st.rerun()
        else: st.sidebar.error("خطأ في البيانات")
else:
    st.sidebar.success(f"المستخدم: {st.session_state['user_name']}")
    if st.sidebar.button("خروج"):
        st.session_state.update({'logged_in': False})
        st.rerun()

    today = date.today()
    tabs = st.tabs(["📊 حالة الوحدات", "➕ إضافة حجز", "📋 السجل العام", "💰 التقارير والتصدير", "⚙️ الإعدادات والهوية"])

    # --- التبويبات (كما هي في الكود السابق مع الحفاظ على البيانات) ---
    with tabs[0]: # حالة الوحدات
        all_u = [r[0] for r in c.execute("SELECT name FROM units_names").fetchall()]
        c.execute("SELECT id, unit_no, client_name FROM bookings WHERE ? >= check_in AND ? < check_out", (today, today))
        occ_data = c.fetchall()
        occ_names = [r[1] for r in occ_data]
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔴 مشغولة")
            for b_id, u_n, c_n in occ_data:
                cx, cb = st.columns([3, 1])
                cx.error(f"🏠 {u_n} - {c_n}")
                if cb.button("إخلاء", key=f"end_{b_id}"):
                    c.execute("UPDATE bookings SET check_out = ? WHERE id = ?", (today, b_id))
                    conn.commit(); st.rerun()
        with c2:
            st.subheader("🟢 فارغة")
            for u in [un for un in all_u if un not in occ_names]:
                cx, cb = st.columns([3, 1])
                cx.success(f"🔑 {u}")
                if cb.button("حجز", key=f"bk_{u}"):
                    st.session_state['selected_unit'] = u
                    st.rerun()

    with tabs[1]: # إضافة حجز
        units_raw = [r[0] for r in c.execute("SELECT name FROM units_names").fetchall()]
        plats_raw = [r[0] for r in c.execute("SELECT name FROM platforms").fetchall()]
        idx = units_raw.index(st.session_state['selected_unit']) if st.session_state['selected_unit'] in units_raw else 0
        with st.form("full_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                u_sel = st.selectbox("الوحدة", units_raw, index=idx) if units_raw else None
                p_sel = st.selectbox("المنصة", plats_raw) if plats_raw else None
                client, phone = st.text_input("العميل"), st.text_input("الهاتف")
            with col2:
                price = st.number_input("السعر", min_value=0.0)
                d_in, d_out = st.date_input("دخول"), st.date_input("خروج")
                u_exp, u_comp = st.number_input("مصروفات"), st.number_input("تعويضات")
            note = st.text_area("ملاحظات")
            file = st.file_uploader("📸 ارفق صورة الفاتورة")
            if st.form_submit_button("حفظ الحجز"):
                path = f"all_bills/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}" if file else ""
                if file:
                    with open(path, "wb") as f: f.write(file.getbuffer())
                c.execute('''INSERT INTO bookings (unit_no, client_name, phone, platform, price, check_in, check_out, expenses, compensations, note, bill_path, added_by) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (u_sel, client, phone, p_sel, price, d_in, d_out, u_exp, u_comp, note, path, st.session_state['user_name']))
                conn.commit(); st.session_state['selected_unit'] = None; st.success("تم الحفظ!"); st.rerun()

    with tabs[2]: # السجل العام
        df_all = pd.read_sql_query("SELECT id, unit_no, client_name, phone, platform, check_in, check_out, added_by FROM bookings", conn)
        st.dataframe(df_all, use_container_width=True)

    with tabs[3]: # التقارير
        df_fin = pd.read_sql_query("SELECT * FROM bookings", conn)
        if not df_fin.empty:
            df_fin['الصافي'] = df_fin['price'] + df_fin['compensations'] - df_fin['expenses']
            st.metric("صافي الأرباح", f"{df_fin['الصافي'].sum()} ر.س")
            st.dataframe(df_fin)
            csv = df_fin.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 تصدير للوكالة (Excel)", csv, "report.csv", "text/csv")

    with tabs[4]: # الإعدادات والهوية (الجديد)
        if st.session_state['user_role'] == "مدير":
            st.subheader("🖼️ إعدادات هوية النظام")
            new_app_name = st.text_input("اسم المنشأة/البرنامج", value=app_name)
            new_logo = st.file_uploader("رفع شعار جديد (Logo)", type=['png', 'jpg', 'jpeg'])
            
            if st.button("تحديث الهوية"):
                c.execute("UPDATE settings SET value=? WHERE key='app_name'", (new_app_name,))
                if new_logo:
                    l_path = f"brand/logo_{new_logo.name}"
                    with open(l_path, "wb") as f: f.write(new_logo.getbuffer())
                    c.execute("INSERT OR REPLACE INTO settings VALUES ('logo_path', ?)", (l_path,))
                conn.commit()
                st.success("تم تحديث الهوية بنجاح!")
                st.rerun()

            st.divider()
            col_u, col_p = st.columns(2)
            with col_u:
                nu = st.text_input("إضافة وحدة")
                if st.button("حفظ الوحدة"): c.execute("INSERT INTO units_names (name) VALUES (?)", (nu,)); conn.commit(); st.rerun()
            with col_p:
                np = st.text_input("إضافة جهة حجز")
                if st.button("حفظ الجهة"): c.execute("INSERT INTO platforms (name) VALUES (?)", (np,)); conn.commit(); st.rerun()
        else:
            st.warning("هذا القسم للمدير فقط")
