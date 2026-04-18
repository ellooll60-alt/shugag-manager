import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime, timedelta

# =========================
# 1) إعدادات Supabase
# =========================
SUPABASE_URL = "https://sdoeyobzknoycovobbvc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNkb2V5b2J6a25veWNvdm9iYnZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDgwNjIsImV4cCI6MjA5MTkyNDA2Mn0.mXmsEgGMbXwjR4tmSYcWYbH7pCjMJDCm-VclIFMVUvI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 2) تهيئة الجلسة
# =========================
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'user_name': "",
        'user_role': "",
        'selected_unit': None,
        'edit_booking': None,
        'language': 'ar',   # ar / en (قابل للتطوير لاحقًا)
        'theme': 'glass',   # light / dark / glass (قابل للتطوير لاحقًا)
    })
if 'edit_booking' not in st.session_state:
    st.session_state.edit_booking = None

# =========================
# 3) إعدادات النظام من Supabase
# =========================
def get_settings():
    try:
        res = supabase.table("settings").select("*").execute()
        return {row['key']: row['value'] for row in res.data} if res.data else {}
    except Exception:
        return {"app_name": "نظام إدارة الوحدات"}

settings = get_settings()
app_name = settings.get('app_name', 'نظام إدارة الوحدات')
logo_url = settings.get('logo_path', '')

st.set_page_config(page_title=app_name, layout="wide")

# =========================
# 4) تصميم الواجهة (Glass Style بسيط)
# =========================
st.markdown("""
<style>
.main {
    background: radial-gradient(circle at top left, #1f2933, #111827);
    color: #f9fafb;
}
.block-container {
    backdrop-filter: blur(18px);
    background: rgba(15, 23, 42, 0.65);
    border-radius: 18px;
    padding: 2rem 2.5rem;
    margin-top: 1.5rem;
}
.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3em;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
    font-weight: 600;
    border: none;
}
.stMetric {
    background-color: rgba(15, 23, 42, 0.85);
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.35);
}
</style>
""", unsafe_allow_html=True)

# =========================
# 5) الهيدر (الشعار + العنوان)
# =========================
c_logo, c_title, c_empty = st.columns([2, 5, 1])
with c_title:
    st.markdown("<h1 style='text-align:center; color:#e5e7eb;'>" + app_name + "</h1>", unsafe_allow_html=True)
with c_logo:
    if logo_url:
        st.image(logo_url, width=120)

st.markdown("---")

# =========================
# 6) تسجيل الدخول
# =========================
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
        st.session_state.user_name = ""
        st.session_state.user_role = ""
        st.session_state.selected_unit = None
        st.session_state.edit_booking = None
        st.rerun()

    # =========================
    # 7) تحميل البيانات الأساسية
    # =========================
    units_res = supabase.table("units_names").select("name").execute()
    units = [r['name'] for r in units_res.data] if units_res.data else []

    plats_res = supabase.table("platforms").select("name").execute()
    plats = [r['name'] for r in plats_res.data] if plats_res.data else []

    today = date.today()

    tabs = st.tabs([
        "📊 حالة الوحدات",
        "➕ حجز جديد",
        "📋 السجل العام",
        "💰 التقارير المالية",
        "⚙️ الإعدادات"
    ])

    # =========================
    # التبويب 1: حالة الوحدات
    # =========================
    with tabs[0]:
        st.subheader("🔍 مراقبة الإشغال اللحظي")

        occ_res = supabase.table("bookings").select("*") \
            .lte("check_in", str(today)) \
            .gt("check_out", str(today)) \
            .execute().data

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

    # =========================
    # التبويب 2: حجز جديد
    # =========================
    with tabs[1]:
        st.subheader("📝 تسجيل حجز جديد")

        idx = units.index(st.session_state.selected_unit) if st.session_state.selected_unit in units else 0

        with st.form("booking_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                u_sel = st.selectbox("الوحدة", units, index=idx if units else 0)
                p_sel = st.selectbox("جهة الحجز", plats)
                client = st.text_input("اسم العميل")
                phone = st.text_input("رقم الهاتف")

            with col2:
                price = st.number_input("سعر الإيجار", min_value=0.0)
                d_in = st.date_input("الدخول", value=today)
                d_out = st.date_input("الخروج", value=today + timedelta(days=1))
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

    # =========================
    # التبويب 3: السجل العام (مع تعديل/حذف + واتساب)
    # =========================
    with tabs[2]:
        st.subheader("📋 سجل الحجوزات")

        search = st.text_input("🔍 بحث بالاسم أو الهاتف")

        bookings = supabase.table("bookings").select("*").order("id", desc=True).execute().data
        df = pd.DataFrame(bookings)

        if df.empty:
            st.info("لا توجد حجوزات")
        else:
            if search:
                df = df[
                    df['client_name'].str.contains(search, na=False) |
                    df['phone'].str.contains(search, na=False)
                ]

            # تنبيه بقرب موعد الخروج (خلال 24 ساعة)
            upcoming = df[
                pd.to_datetime(df['check_out']) <= (pd.to_datetime(today) + pd.Timedelta(days=1))
            ]
            if not upcoming.empty:
                st.warning("⏰ حجوزات يقترب موعد خروجها:")
                for _, r in upcoming.iterrows():
                    msg = f"تنبيه: موعد خروجك من الوحدة {r['unit_no']} بتاريخ {r['check_out']}"
                    wa_url = f"https://wa.me/{r['phone']}?text={msg}"
                    st.markdown(
                        f"- {r['client_name']} - {r['unit_no']} - {r['check_out']} | [إرسال واتساب]({wa_url})",
                        unsafe_allow_html=True
                    )

            st.markdown("### القائمة التفصيلية")
            for _, row in df.iterrows():
                with st.expander(f"🏠 {row['unit_no']} | {row['client_name']}"):
                    st.write(f"📱 الهاتف: {row.get('phone', '')}")
                    st.write(f"💵 السعر: {row['price']}")
                    st.write(f"📅 من: {row['check_in']} إلى {row['check_out']}")
                    st.write(f"🔗 المنصة: {row['platform']}")
                    st.write(f"📝 ملاحظات: {row.get('note', '')}")
                    st.write(f"👤 أضيف بواسطة: {row.get('added_by', '')}")

                    c1, c2, c3 = st.columns(3)
                    if c1.button("✏️ تعديل", key=f"edit_{row['id']}"):
                        st.session_state.edit_booking = dict(row)
                        st.rerun()
                    if c2.button("🗑️ حذف", key=f"del_{row['id']}"):
                        supabase.table("bookings").delete().eq("id", row['id']).execute()
                        st.success("تم حذف الحجز")
                        st.rerun()
                    msg = f"تفاصيل حجزك في الوحدة {row['unit_no']} من {row['check_in']} إلى {row['check_out']}"
                    wa_url = f"https://wa.me/{row['phone']}?text={msg}"
                    c3.markdown(f"[📲 واتساب للعميل]({wa_url})", unsafe_allow_html=True)

            # نافذة تعديل الحجز
            if st.session_state.edit_booking:
                st.markdown("---")
                st.subheader("✏️ تعديل الحجز")
                b = st.session_state.edit_booking

                with st.form("edit_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        u_sel = st.selectbox("الوحدة", units, index=units.index(b["unit_no"]) if b["unit_no"] in units else 0)
                        client = st.text_input("اسم العميل", b["client_name"])
                        phone = st.text_input("رقم الهاتف", b.get("phone", ""))
                        p_sel = st.selectbox("جهة الحجز", plats, index=plats.index(b["platform"]) if b["platform"] in plats else 0)
                    with col2:
                        price = st.number_input("سعر الإيجار", value=float(b["price"]))
                        d_in = st.date_input("الدخول", value=pd.to_datetime(b["check_in"]))
                        d_out = st.date_input("الخروج", value=pd.to_datetime(b["check_out"]))
                        exp = st.number_input("مصروفات إضافية", value=float(b.get("expenses", 0)))
                        comp = st.number_input("تعويضات", value=float(b.get("compensations", 0)))

                    note = st.text_area("ملاحظات", b.get("note", ""))

                    if st.form_submit_button("💾 حفظ التعديلات"):
                        supabase.table("bookings").update({
                            "unit_no": u_sel,
                            "client_name": client,
                            "phone": phone,
                            "platform": p_sel,
                            "price": price,
                            "check_in": str(d_in),
                            "check_out": str(d_out),
                            "expenses": exp,
                            "compensations": comp,
                            "note": note
                        }).eq("id", b["id"]).execute()
                        st.success("تم تحديث الحجز")
                        st.session_state.edit_booking = None
                        st.rerun()

    # =========================
    # التبويب 4: التقارير المالية
    # =========================
    with tabs[3]:
        st.subheader("💰 التقارير المالية")

        bookings = supabase.table("bookings").select("*").execute().data
        df = pd.DataFrame(bookings)

        if df.empty:
            st.info("لا توجد بيانات مالية")
        else:
            df['الصافي'] = df['price'] + df['compensations'] - df['expenses']
            df['month'] = pd.to_datetime(df['check_in']).dt.to_period('M').astype(str)

            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الدخل", f"{df['price'].sum():,.2f} ريال")
            c2.metric("إجمالي المصاريف", f"{df['expenses'].sum():,.2f} ريال")
            c3.metric("صافي الربح", f"{df['الصافي'].sum():,.2f} ريال")

            st.markdown("### حسب الشهر")
            monthly = df.groupby('month')[['price', 'expenses', 'الصافي']].sum().reset_index()
            st.dataframe(monthly, use_container_width=True)

            st.markdown("### جميع العمليات")
            st.dataframe(df, use_container_width=True)

    # =========================
    # التبويب 5: الإعدادات
    # =========================
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

                st.write("📌 الشعار (رابط صورة)")
                new_logo = st.text_input("رابط الشعار", value=logo_url)
                if st.button("تحديث الشعار"):
                    supabase.table("settings").upsert({"key": "logo_path", "value": new_logo}).execute()
                    st.success("تم التحديث")
                    st.rerun()

                st.divider()
                st.write("🏢 إدارة الوحدات")
                new_unit = st.text_input("اسم وحدة جديدة")
                if st.button("إضافة وحدة"):
                    if new_unit:
                        supabase.table("units_names").insert({"name": new_unit}).execute()
                        st.success("تمت الإضافة")
                        st.rerun()

            # --- الموظفين وجهات الحجز ---
            with col2:
                st.write("👥 الموظفين")
                mu = st.text_input("اسم مستخدم جديد")
                mp = st.text_input("كلمة المرور")
                if st.button("إضافة مستخدم"):
                    if mu and mp:
                        supabase.table("users").insert({"username": mu, "password": mp, "role": "موظف"}).execute()
                        st.success("تمت الإضافة")

                st.divider()
                st.write("🔗 جهات الحجز")
                np = st.text_input("جهة حجز جديدة")
                if st.button("إضافة جهة"):
                    if np:
                        supabase.table("platforms").insert({"name": np}).execute()
                        st.success("تمت الإضافة")
                        st.rerun()

            st.divider()
            st.write("🗑️ حذف حجز برقم ID")
            delete_id = st.number_input("ID حذف نهائي", min_value=1, step=1)
            if st.button("حذف الحجز"):
                supabase.table("bookings").delete().eq("id", delete_id).execute()
                st.success("تم الحذف")
                st.rerun()


