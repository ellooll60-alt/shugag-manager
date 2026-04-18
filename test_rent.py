import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# --- 1. إعدادات Supabase ---
URL = "https://sdoeyobzknoycovobbvc.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNkb2V5b2J6a25veWNvdm9iYnZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDgwNjIsImV4cCI6MjA5MTkyNDA2Mn0.mXmsEgGMbXwjR4tmSYcWYbH7pCjMJDCm-VclIFMVUvI"

supabase = create_client(URL, KEY)

# --- 2. تهيئة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user_name': "",
        'user_role': "",
        'selected_unit': None
    })

# --- 3. إعدادات النظام ---
def get_settings():
    try:
        res = supabase.table("settings").select("*").execute()
        return {row['key']: row['value'] for row in res.data} if res.data else {}
    except:
        return {"app_name": "نظام إدارة الوحدات"}

settings = get_settings()
app_name = settings.get('app_name', 'نظام إدارة الوحدات')
logo_url = settings.get('logo_path', '')

st.set_page_config(page_title=app_name, layout="wide")

# --- 4. تصميم الواجهة ---
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
.stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

col_l, col_t = st.columns([1, 5])
if logo_url:
    col_l.image(logo_url, width=80)
col_t.title(app_name)

# --- 5. تسجيل الدخول ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 دخول النظام")
    with st.sidebar.form("login_form"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.logged_in = True
                st.session_state.user_name = res.data[0]['username']
                st.session_state.user_role = res.data[0]['role']
                st.rerun()
            else:
                st.sidebar.error("❌ بيانات خاطئة")
else:
    st.sidebar.success(f"👤 {st.session_state.user_name} ({st.session_state.user_role})")
    if st.sidebar.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 6. تحميل البيانات الأساسية ---
    units = [r['name'] for r in supabase.table("units_names").select("name").execute().data]
    plats = [r['name'] for r in supabase.table("platforms").select("name").execute().data]

    today = date.today()
    tabs = st.tabs(["📊 حالة الوحدات", "➕ حجز جديد", "📋 السجل العام", "💰 التقارير المالية", "⚙️ الإعدادات"])

    # --- التبويب 1: حالة الوحدات ---
    with tabs[0]:
        st.subheader("🔍 مراقبة الإشغال اللحظي")

        occ_res = supabase.table("bookings").select("*").lte("check_in", str(today)).gt("check_out", str(today)).execute().data
        occ_names = [r['unit_no'] for r in occ_res] if occ_res else []

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### 🔴 مشغولة الآن")
            if occ_res:
                for r in occ_res:
                    col_i, col_b = st.columns([3, 1])
                    col_i.error(f"🏠 {r['unit_no']} - {r['client_name']}")
                    if col_b.button("إخلاء", key=f"e_{r['id']}"):
                        supabase.table("bookings").update({"check_out": str(today)}).eq("id", r['id']).execute()
                        st.rerun()
            else:
                st.info("لا توجد وحدات مشغولة")

        with c2:
            st.markdown("#### 🟢 فارغة ومتاحة")
            for u in [un for un in units if un not in occ_names]:
                col_i, col_b = st.columns([3, 1])
                col_i.success(f"🔑 {u}")
                if col_b.button("حجز", key=f"b_{u}"):
                    st.session_state.selected_unit = u
                    st.rerun()

    # --- التبويب 2: إضافة حجز ---
    with tabs[1]:
        st.subheader("📝 تسجيل حجز جديد")

        idx = units.index(st.session_state.selected_unit) if st.session_state.selected_unit in units else 0

        with st.form("booking_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                u_sel = st.selectbox("الوحدة", units, index=idx)
                p_sel = st.selectbox("جهة الحجز", plats)
                client = st.text_input("اسم العميل")
                phone = st.text_input("رقم الهاتف")

            with col2:
                price = st.number_input("سعر الإيجار", min_value=0.0)
                d_in = st.date_input("الدخول", value=today)
                d_out = st.date_input("الخروج")
                exp = st.number_input("مصروفات إضافية", min_value=0.0)
                comp = st.number_input("تعويضات", min_value=0.0)

            note = st.text_area("ملاحظات")

            if st.form_submit_button("✅ حفظ"):
                data = {
                    "unit_no": u_sel,
                    "client_name": client,
                    "phone": phone,
                    "platform": p_sel,
                    "price": price,
                    "check_in": str(d_in),
                    "check_out": str(d_out),
                    "expenses": exp,
                    "compensations": comp,
                    "note": note,
                    "added_by": st.session_state.user_name
                }
                supabase.table("bookings").insert(data).execute()
                st.success("تم الحفظ بنجاح")
                st.session_state.selected_unit = None
                st.rerun()

    # --- التبويب 3: السجل العام ---
    with tabs[2]:
        st.subheader("📋 سجل الحجوزات")
    search = st.text_input("🔍 بحث بالاسم أو الهاتف")

    bookings = supabase.table("bookings").select("*").execute().data
    df = pd.DataFrame(bookings)

    if not df.empty:
        if search:
            df = df[df['client_name'].str.contains(search) | df['phone'].str.contains(search)]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("لا توجد حجوزات")

        if not df.empty:
            if search:
                df = df[df['client_name'].str.contains(search) | df['phone'].str.contains(search)]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا توجد حجوزات")

    # --- التبويب 4: التقارير المالية ---
    with tabs[3]:
        st.subheader("💰 التقارير المالية")

        bookings = supabase.table("bookings").select("*").execute().data
        df = pd.DataFrame(bookings)

        if not df.empty:
            df['الصافي'] = df['price'] + df['compensations'] - df['expenses']

            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الدخل", f"{df['price'].sum()} ريال")
            c2.metric("إجمالي المصاريف", f"{df['expenses'].sum()} ريال")
            c3.metric("صافي الربح", f"{df['الصافي'].sum()} ريال")

            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا توجد بيانات مالية")

    # --- التبويب 5: الإعدادات ---
    with tabs[4]:
        if st.session_state.user_role != "مدير":
            st.warning("هذا القسم مخصص للمدير فقط")
        else:
            st.subheader("⚙️ إعدادات النظام")

            col1, col2 = st.columns(2)

            # --- الهوية والوحدات ---
            with col1:
                st.write("🖼️ الهوية")
                new_name = st.text_input("اسم البرنامج", value=app_name)
                if st.button("تحديث الاسم"):
                    supabase.table("settings").upsert({"key": "app_name", "value": new_name}).execute()
                    st.success("تم التحديث")
                    st.rerun()

                st.divider()
                st.write("🏢 إدارة الوحدات")
                new_unit = st.text_input("اسم وحدة جديدة")
                if st.button("إضافة وحدة"):
                    supabase.table("units_names").insert({"name": new_unit}).execute()
                    st.success("تمت الإضافة")
                    st.rerun()

            # --- الموظفين وجهات الحجز ---
            with col2:
                st.write("👥 الموظفين")
                mu = st.text_input("اسم المستخدم")
                mp = st.text_input("كلمة المرور")
                if st.button("إضافة مستخدم"):
                    supabase.table("users").insert({"username": mu, "password": mp, "role": "موظف"}).execute()
                    st.success("تمت الإضافة")

                st.divider()
                st.write("🔗 جهات الحجز")
                np = st.text_input("جهة حجز جديدة")
                if st.button("إضافة جهة"):
                    supabase.table("platforms").insert({"name": np}).execute()
                    st.success("تمت الإضافة")
                    st.rerun()

            st.divider()
            delete_id = st.number_input("ID حذف نهائي", min_value=1)
            if st.button("🗑️ حذف الحجز"):
                supabase.table("bookings").delete().eq("id", delete_id).execute()
                st.success("تم الحذف")
                st.rerun()



