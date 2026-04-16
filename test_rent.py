import streamlit as st
import pandas as pd
from supabase import create_client
import os
from datetime import datetime, date

# --- 1. إعدادات الربط السحابي ---
URL = "https://supabase.co"
KEY = "sb_publishable_PSSSQPVdXIjYUXnaksqDNA_ikMQd1_-"
supabase = create_client(URL, KEY)

# --- 2. تهيئة الجلسة والهوية ---
if 'logged_in' not in st.session_state: 
    st.session_state.update({'logged_in': False, 'user_name': "", 'user_role': "", 'selected_unit': None})

def get_settings():
    try:
        res = supabase.table("settings").select("*").execute()
        return {row['key']: row['value'] for row in res.data} if res.data else {}
    except: return {"app_name": "نظام إدارة الوحدات"}

settings = get_settings()
app_name = settings.get('app_name', 'نظام إدارة الوحدات')
logo_url = settings.get('logo_path', '')

st.set_page_config(page_title=app_name, layout="wide")

# --- 3. تصميم الواجهة (UI) ---
st.markdown(f"""
    <style>
    .main {{ background-color: #f8f9fa; }}
    .stButton>button {{ width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }}
    .stMetric {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    </style>
    """, unsafe_allow_html=True)

# عرض الشعار والاسم في الأعلى
col_l, col_t = st.columns([1, 5])
if logo_url: col_l.image(logo_url, width=80)
col_t.title(app_name)

# --- 4. نظام تسجيل الدخول ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 دخول النظام")
    with st.sidebar.form("login_form"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            try:
                res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
                if res.data:
                    st.session_state.update({'logged_in': True, 'user_name': u, 'user_role': res.data[0]['role']})
                    st.rerun()
                else: st.sidebar.error("❌ بيانات خاطئة")
            except: st.sidebar.error("⚠️ خطأ: تأكد من جدول users في السحابة")
else:
    st.sidebar.success(f"👤 {st.session_state.user_name} ({st.session_state.user_role})")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.update({'logged_in': False})
        st.rerun()

    # جلب البيانات الأساسية
    try:
        units = [r['name'] for r in supabase.table("units_names").select("name").execute().data]
        plats = [r['name'] for r in supabase.table("platforms").select("name").execute().data]
    except: units, plats = [], []
    
    today = date.today()
    tabs = st.tabs(["📊 حالة الوحدات", "➕ حجز جديد", "📋 السجل العام", "💰 التقارير المالية", "⚙️ الإعدادات"])

    # --- التبويب 1: حالة الوحدات (حجز وإخلاء مباشر) ---
    with tabs[0]:
        st.subheader("🔍 مراقبة الإشغال اللحظي")
        occ_res = supabase.table("bookings").select("*").lte("check_in", str(today)).gt("check_out", str(today)).execute().data
        occ_names = [r['unit_no'] for r in occ_res] if occ_res else []
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🔴 مشغولة الآن")
            for r in occ_res:
                col_i, col_b = st.columns([3,1])
                col_i.error(f"🏠 {r['unit_no']} - {r['client_name']}")
                if col_b.button("إخلاء", key=f"e_{r['id']}"):
                    supabase.table("bookings").update({"check_out": str(today)}).eq("id", r['id']).execute()
                    st.rerun()
        with c2:
            st.markdown("#### 🟢 فارغة ومتاحة")
            for u in [un for un in units if un not in occ_names]:
                col_i, col_b = st.columns([3,1])
                col_i.success(f"🔑 {u}")
                if col_b.button("حجز", key=f"b_{u}"):
                    st.session_state.selected_unit = u
                    st.rerun()

    # --- التبويب 2: إضافة حجز ومصروفات وتعويضات ---
    with tabs[1]:
        st.subheader("📝 تسجيل حجز جديد")
        idx = units.index(st.session_state.selected_unit) if st.session_state.selected_unit in units else 0
        with st.form("main_booking_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                u_sel = st.selectbox("الوحدة", units, index=idx) if units else st.info("أضف وحدات أولاً")
                p_sel = st.selectbox("جهة الحجز", plats) if plats else st.info("أضف منصات أولاً")
                client = st.text_input("اسم العميل")
                phone = st.text_input("رقم الهاتف")
            with col2:
                price = st.number_input("سعر الإيجار", min_value=0.0)
                d_in = st.date_input("الدخول", value=today)
                d_out = st.date_input("الخروج")
                exp = st.number_input("مصروفات إضافية", min_value=0.0)
                comp = st.number_input("تعويضات", min_value=0.0)
            note = st.text_area("ملاحظات")
            if st.form_submit_button("✅ حفظ في السحابة"):
                data = {"unit_no": u_sel, "client_name": client, "phone": phone, "platform": p_sel, 
                        "price": price, "check_in": str(d_in), "check_out": str(d_out), 
                        "expenses": exp, "compensations": comp, "note": note, "added_by": st.session_state.user_name}
                supabase.table("bookings").insert(data).execute()
                st.session_state.selected_unit = None
                st.success("تم الحفظ بنجاح!")
                st.rerun()

    # --- التبويب 3: السجل العام والبحث برقم الهاتف ---
    with tabs[2]:
        st.subheader("📋 سجل الحجوزات")
        search = st.text_input("🔍 بحث برقم الهاتف أو الاسم")
        bookings_data = supabase.table("bookings").select("*").execute().data
        df = pd.DataFrame(bookings_data) if bookings_data else pd.DataFrame()
        if not df.empty:
            if search: df = df[df['client_name'].str.contains(search) | df['phone'].str.contains(search)]
            st.dataframe(df[['unit_no', 'client_name', 'phone', 'platform', 'check_in', 'check_out', 'added_by']], use_container_width=True)

    # --- التبويب 4: التقارير المالية وتحليل الأرباح ---
    with tabs[3]:
        if not df.empty:
            df['الصافي'] = df['price'] + df['compensations'] - df['expenses']
            m1, m2, m3 = st.columns(3)
            m1.metric("إجمالي الدخل", f"{df['price'].sum()} ريال")
            m2.metric("إجمالي المصاريف", f"{df['expenses'].sum()} ريال")
            m3.metric("صافي الربح", f"{df['الصافي'].sum()} ريال")
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 تصدير للوكالة (Excel)", df.to_csv(index=False).encode('utf-8-sig'), "financial_report.csv")

    # --- التبويب 5: الإعدادات (الهوية، الوحدات، الموظفين، الحذف) ---
    with tabs[4]:
        if st.session_state.user_role == "مدير":
            st.subheader("⚙️ إعدادات النظام")
            col_admin1, col_admin2 = st.columns(2)
            with col_admin1:
                st.write("🖼️ الهوية")
                new_n = st.text_input("تغيير اسم البرنامج", value=app_name)
                if st.button("تحديث الاسم"):
                    supabase.table("settings").upsert({"key": "app_name", "value": new_n}).execute()
                    st.rerun()
                st.divider()
                st.write("🏢 إدارة الوحدات")
                nu = st.text_input("اسم وحدة جديدة")
                if st.button("حفظ الوحدة"):
                    supabase.table("units_names").insert({"name": nu}).execute(); st.rerun()
            with col_admin2:
                st.write("👥 الموظفين")
                mu, mp = st.text_input("اسم المستخدم"), st.text_input("كلمة المرور")
                if st.button("إضافة مستخدم"):
                    supabase.table("users").insert({"username": mu, "password": mp, "role": "موظف"}).execute()
                    st.success(f"تمت إضافة {mu}")
                st.divider()
                st.write("🔗 جهات الحجز")
                np = st.text_input("جهة حجز جديدة")
                if st.button("إضافة جهة"):
                    supabase.table("platforms").insert({"name": np}).execute(); st.rerun()
            
            st.divider()
            did = st.number_input("أدخل ID الحجز للحذف النهائي", min_value=1)
            if st.button("🗑️ حذف الحجز نهائياً"):
                supabase.table("bookings").delete().eq("id", did).execute(); st.rerun()
        else: st.warning("هذا القسم مخصص للمدير فقط")


