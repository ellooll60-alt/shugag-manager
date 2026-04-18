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
        'background_image': None
    })

# =========================
# 3) تحميل الإعدادات من Supabase
# =========================
def get_settings():
    try:
        res = supabase.table("settings").select("*").execute()
        return {row['key']: row['value'] for row in res.data} if res.data else {}
    except:
        return {}

settings = get_settings()
app_name = settings.get("app_name", "نظام إدارة الوحدات")
logo_url = settings.get("logo_path", "")
background_image = settings.get("background_image", "")

st.set_page_config(page_title=app_name, layout="wide")

# =========================
# 4) تصميم الخلفية (Light Glass Mode + دعم صورة Cover)
# =========================
if background_image:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url('{background_image}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .block-container {{
            background: rgba(255, 255, 255, 0.55);
            backdrop-filter: blur(12px);
            border-radius: 18px;
            padding: 2rem 2.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        .stApp {
            background: rgba(255, 255, 255, 0.35);
        }
        .block-container {
            background: rgba(255, 255, 255, 0.55);
            backdrop-filter: blur(12px);
            border-radius: 18px;
            padding: 2rem 2.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
# =========================
# 5) الهيدر العلوي (الشعار + العنوان)
# =========================
c_logo, c_title, c_empty = st.columns([2, 5, 1])

with c_title:
    st.markdown(
        f"<h1 style='text-align:center; color:#111827; margin-bottom:0.5rem;'>{app_name}</h1>",
        unsafe_allow_html=True
    )

with c_logo:
    if logo_url:
        st.image(logo_url, width=110)

st.markdown("<hr style='margin-top:0.5rem; margin-bottom:1rem;'>", unsafe_allow_html=True)

# =========================
# 6) تسجيل الدخول / الخروج
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
                st.session_state.user_name = res.data[0]["username"]
                st.session_state.user_role = res.data[0]["role"]
                st.experimental_rerun()
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
        st.experimental_rerun()

# =========================
# 7) تحميل البيانات الأساسية + إنشاء التبويبات
# =========================
if st.session_state.logged_in:
    # تحميل أسماء الوحدات
    units_res = supabase.table("units_names").select("name").execute()
    units = [r["name"] for r in units_res.data] if units_res.data else []

    # تحميل المنصات
    plats_res = supabase.table("platforms").select("name").execute()
    plats = [r["name"] for r in plats_res.data] if plats_res.data else []

    today = date.today()

    tabs = st.tabs([
        "📊 حالة الوحدات",
        "➕ حجز جديد",
        "📋 السجل العام",
        "💰 التقارير المالية",
        "⚙️ الإعدادات"
    ])
# =========================================================
# 📊 التبويب الأول: حالة الوحدات
# =========================================================
with tabs[0]:
    st.subheader("📊 حالة الوحدات")

    # جلب الحجوزات الحالية
    bookings_res = supabase.table("bookings").select("*").execute()
    bookings = bookings_res.data if bookings_res.data else []

    occupied_units = [b["unit"] for b in bookings if b.get("status", "مشغول") == "مشغول"]
    free_units = [u for u in units if u not in occupied_units]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🟢 الوحدات الشاغرة")
        if free_units:
            for u in free_units:
                if st.button(f"حجز {u}", key=f"free_{u}"):
                    st.session_state.selected_unit = u
                    st.experimental_rerun()
        else:
            st.info("لا توجد وحدات شاغرة حالياً")

    with col2:
        st.markdown("### 🔴 الوحدات المشغولة")
        if occupied_units:
            for u in occupied_units:
                if st.button(f"إخلاء {u}", key=f"occ_{u}"):
                    supabase.table("bookings").delete().eq("unit", u).execute()
                    st.success(f"تم إخلاء الوحدة {u}")
                    st.experimental_rerun()
        else:
            st.info("لا توجد وحدات مشغولة حالياً")

# =========================================================
# ➕ التبويب الثاني: إضافة حجز جديد
# =========================================================
with tabs[1]:
    st.subheader("➕ إضافة حجز جديد")

    with st.form("new_booking_form"):
        unit = st.selectbox("اختر الوحدة", units)
        platform = st.selectbox("منصة الحجز", plats)
        guest = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        check_in = st.date_input("تاريخ الدخول", date.today())
        check_out = st.date_input("تاريخ الخروج", date.today() + timedelta(days=1))
        price = st.number_input("السعر", min_value=0)
        expenses = st.number_input("المصاريف", min_value=0)
        compensation = st.number_input("التعويضات", min_value=0)
        notes = st.text_area("ملاحظات")

        submitted = st.form_submit_button("💾 حفظ الحجز")

        if submitted:
            supabase.table("bookings").insert({
                "unit": unit,
                "platform": platform,
                "guest": guest,
                "phone": phone,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "price": price,
                "expenses": expenses,
                "compensation": compensation,
                "notes": notes,
                "status": "مشغول"
            }).execute()

            st.success("تم إضافة الحجز بنجاح")
            st.experimental_rerun()
# =========================================================
# 📋 التبويب الثالث: السجل العام
# =========================================================
with tabs[2]:
    st.subheader("📋 السجل العام")

    # جلب جميع الحجوزات
    all_res = supabase.table("bookings").select("*").order("id", desc=True).execute()
    all_bookings = all_res.data if all_res.data else []

    # 🔍 البحث
    search = st.text_input("🔍 بحث بالاسم أو رقم الهاتف")

    if search:
        all_bookings = [
            b for b in all_bookings
            if search in b["guest"] or search in b["phone"]
        ]

    # 🔔 تنبيه بقرب الخروج (خلال 24 ساعة)
    st.markdown("### 🔔 حجوزات يقترب موعد خروجها")
    near_exit = [
        b for b in all_bookings
        if datetime.strptime(b["check_out"], "%Y-%m-%d").date() <= date.today() + timedelta(days=1)
    ]

    if near_exit:
        for b in near_exit:
            st.warning(f"الوحدة {b['unit']} — العميل {b['guest']} — الخروج: {b['check_out']}")
    else:
        st.info("لا توجد حجوزات يقترب موعد خروجها")

    st.markdown("---")

    # عرض الحجوزات
    for b in all_bookings:
        with st.expander(f"📌 {b['unit']} — {b['guest']} — {b['check_in']} → {b['check_out']}"):
            st.write(f"**العميل:** {b['guest']}")
            st.write(f"**الهاتف:** {b['phone']}")
            st.write(f"**المنصة:** {b['platform']}")
            st.write(f"**السعر:** {b['price']}")
            st.write(f"**المصاريف:** {b['expenses']}")
            st.write(f"**التعويضات:** {b['compensation']}")
            st.write(f"**ملاحظات:** {b['notes']}")

            colA, colB, colC = st.columns(3)

            # زر واتساب
            with colA:
                msg = f"مرحباً {b['guest']}، نذكرك بأن موعد خروجك من الوحدة {b['unit']} هو {b['check_out']}."
                wa = f"https://wa.me/{b['phone']}?text={msg}"
                st.markdown(f"[📱 واتساب]({wa})")

            # زر تعديل
            with colB:
                if st.button("✏️ تعديل", key=f"edit_{b['id']}"):
                    st.session_state.edit_booking = b
                    st.experimental_rerun()

            # زر حذف
            with colC:
                if st.button("🗑️ حذف", key=f"del_{b['id']}"):
                    supabase.table("bookings").delete().eq("id", b["id"]).execute()
                    st.error("تم حذف الحجز")
                    st.experimental_rerun()

    # نافذة تعديل الحجز
    if st.session_state.edit_booking:
        st.markdown("## ✏️ تعديل الحجز")
        edit = st.session_state.edit_booking

        with st.form("edit_form"):
            unit = st.select
            # =========================================================
# 💰 التبويب الرابع: التقارير المالية
# =========================================================
with tabs[3]:
    st.subheader("💰 التقارير المالية")

    # جلب جميع الحجوزات
    fin_res = supabase.table("bookings").select("*").execute()
    fin = fin_res.data if fin_res.data else []

    if not fin:
        st.info("لا توجد بيانات مالية حالياً")
    else:
        # حساب الإجماليات
        total_income = sum(b["price"] for b in fin)
        total_expenses = sum(b["expenses"] for b in fin)
        total_compensation = sum(b["compensation"] for b in fin)
        net_profit = total_income - total_expenses + total_compensation

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("💵 إجمالي الدخل", f"{total_income} ريال")

        with col2:
            st.metric("💸 إجمالي المصاريف", f"{total_expenses} ريال")

        with col3:
            st.metric("⚠️ التعويضات", f"{total_compensation} ريال")

        with col4:
            st.metric("📈 صافي الربح", f"{net_profit} ريال")

        st.markdown("---")

        # تقرير شهري
        st.markdown("### 📅 تقرير شهري")

        months = sorted(
            list(
                set(
                    datetime.strptime(b["check_in"], "%Y-%m-%d").strftime("%Y-%m")
                    for b in fin
                )
            )
        )

        selected_month = st.selectbox("اختر الشهر", months)

        month_data = [
            b for b in fin
            if datetime.strptime(b["check_in"], "%Y-%m-%d").strftime("%Y-%m") == selected_month
        ]

        if month_data:
            m_income = sum(b["price"] for b in month_data)
            m_expenses = sum(b["expenses"] for b in month_data)
            m_comp = sum(b["compensation"] for b in month_data)
            m_net = m_income - m_expenses + m_comp

            st.write(f"**💵 الدخل:** {m_income} ريال")
            st.write(f"**💸 المصاريف:** {m_expenses} ريال")
            st.write(f"**⚠️ التعويضات:** {m_comp} ريال")
            st.write(f"**📈 الصافي:** {m_net} ريال")

            st.markdown("#### تفاصيل العمليات")
            st.dataframe(pd.DataFrame(month_data))
        else:
            st.info("لا توجد بيانات لهذا الشهر")
# =========================================================
# ⚙️ التبويب الخامس: الإعدادات
# =========================================================
with tabs[4]:

    if st.session_state.user_role != "admin":
        st.error("❌ هذه الصفحة مخصصة للمدير فقط")
    else:
        st.subheader("⚙️ إعدادات النظام")

        # -------------------------------------------------
        # 1) تغيير اسم البرنامج
        # -------------------------------------------------
        st.markdown("### 📝 تغيير اسم البرنامج")

        new_name = st.text_input("اسم البرنامج", value=app_name)
        if st.button("💾 حفظ الاسم"):
            supabase.table("settings").upsert({"key": "app_name", "value": new_name}).execute()
            st.success("تم تحديث اسم البرنامج")
            st.experimental_rerun()

        st.markdown("---")

        # -------------------------------------------------
        # 2) تغيير الشعار
        # -------------------------------------------------
        st.markdown("### 🖼️ تغيير الشعار")

        new_logo = st.text_input("رابط الشعار", value=logo_url)
        if st.button("💾 حفظ الشعار"):
            supabase.table("settings").upsert({"key": "logo_path", "value": new_logo}).execute()
            st.success("تم تحديث الشعار")
            st.experimental_rerun()

        st.markdown("---")

        # -------------------------------------------------
        # 3) إعدادات الخلفية (شفافة + رفع صورة + رابط صورة + إزالة)
        # -------------------------------------------------
        st.markdown("### 🎨 إعدادات الخلفية")

        st.info("الخلفية الافتراضية: شفافة (Light Glass Mode)")

        # رفع صورة خلفية
        bg_file = st.file_uploader("رفع صورة خلفية (JPG / PNG)", type=["jpg", "jpeg", "png"])

        if bg_file:
            import base64
            bg_bytes = bg_file.read()
            bg_base64 = base64.b64encode(bg_bytes).decode()
            bg_url = f"data:image/png;base64,{bg_base64}"

            if st.button("💾 حفظ الخلفية المرفوعة"):
                supabase.table("settings").upsert({"key": "background_image", "value": bg_url}).execute()
                st.success("تم تحديث الخلفية")
                st.experimental_rerun()

        # رابط صورة خلفية
        bg_link = st.text_input("أو ضع رابط صورة خلفية", value=background_image)

        if st.button("💾 حفظ رابط الخلفية"):
            supabase.table("settings").upsert({"key": "background_image", "value": bg_link}).execute()
            st.success("تم تحديث الخلفية")
            st.experimental_rerun()

        # إزالة الخلفية
        if st.button("🗑️ إزالة الخلفية والعودة للوضع الشفاف"):
            supabase.table("settings").upsert({"key": "background_image", "value": ""}).execute()
            st.success("تمت إزالة الخلفية")
            st.experimental_rerun()

        st.markdown("---")

        # -------------------------------------------------
        # 4) إضافة وحدة جديدة
        # -------------------------------------------------
        st.markdown("### 🏠 إضافة وحدة جديدة")

        new_unit = st.text_input("اسم الوحدة الجديدة")
        if st.button("➕ إضافة الوحدة"):
            if new_unit:
                supabase.table("units_names").insert({"name": new_unit}).execute()
                st.success("تمت إضافة الوحدة")
                st.experimental_rerun()
            else:
                st.error("الرجاء إدخال اسم الوحدة")

        st.markdown("---")

        # -------------------------------------------------
        # 5) إضافة منصة جديدة
        # -------------------------------------------------
        st.markdown("### 🌐 إضافة منصة جديدة")

        new_platform = st.text_input("اسم المنصة الجديدة")
        if st.button("➕ إضافة المنصة"):
            if new_platform:
                supabase.table("platforms").insert({"name": new_platform}).execute()
                st.success("تمت إضافة المنصة")
                st.experimental_rerun()
            else:
                st.error("الرجاء إدخال اسم المنصة")

        st.markdown("---")

        # -------------------------------------------------
        # 6) إضافة مستخدم جديد
        # -------------------------------------------------
        st.markdown("### 👤 إضافة مستخدم جديد")

        col_u1, col_u2 = st.columns(2)

        with col_u1:
            new_user = st.text_input("اسم المستخدم الجديد")

        with col_u2:
            new_pass = st.text_input("كلمة المرور", type="password")

        new_role = st.selectbox("الصلاحية", ["admin", "user"])

        if st.button("➕ إضافة المستخدم"):
            if new_user and new_pass:
                supabase.table("users").insert({
                    "username": new_user,
                    "password": new_pass,
                    "role": new_role
                }).execute()
                st.success("تمت إضافة المستخدم")
            else:
                st.error("الرجاء إدخال جميع البيانات")

        st.markdown("---")

        # -------------------------------------------------
        # 7) حذف حجز برقم ID (للطوارئ)
        # -------------------------------------------------
        st.markdown("### 🗑️ حذف حجز برقم ID")

        del_id = st.number_input("رقم الحجز", min_value=1)

        if st.button("❌ حذف الحجز"):
            supabase.table("bookings").delete().eq("id", del_id).execute()
            st.success("تم حذف الحجز")
# =========================================================
# 🎉 نهاية الملف
# =========================================================

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; opacity:0.6;'>"
    "تم تطوير هذا النظام باستخدام Streamlit + Supabase<br>"
    "جميع الحقوق محفوظة ©"
    "</p>",
    unsafe_allow_html=True
)
