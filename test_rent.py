import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime, timedelta
import base64

# =========================
# 1) إعدادات Supabase
# =========================
SUPABASE_URL = "https://sdoeyobzknoycovobbvc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNkb2V5b2J6a25veWNvdm9iYnZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzNDgwNjIsImV4cCI6MjA5MTkyNDA2Mn0.mXmsEgGMbXwjR4tmSYcWYbH7pCjMJDCm-VclIFMVUvI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# 2) تهيئة الجلسة
# =========================
if "logged_in" not in st.session_state:
    st.session_state.update({
        "logged_in": False,
        "user_name": "",
        "user_role": "",
        "selected_unit": None,
        "edit_booking": None
    })

# =========================
# 3) تحميل الإعدادات
# =========================
def load_settings():
    try:
        res = supabase.table("settings").select("*").execute()
        data = res.data or []
        return {row["key"]: row["value"] for row in data}
    except:
        return {}

settings = load_settings()

app_name = settings.get("app_name", "نظام إدارة الوحدات")
logo_url = settings.get("logo_path", "")
background_image = settings.get("background_image", "")

st.set_page_config(page_title=app_name, layout="wide")

# =========================
# 4) الخلفية
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

# =========================
# 5) الهيدر
# =========================
c_logo, c_title, c_empty = st.columns([2, 5, 1])

with c_title:
    st.markdown(
        f"<h1 style='text-align:center; color:#111827;'>{app_name}</h1>",
        unsafe_allow_html=True
    )

with c_logo:
    if logo_url:
        st.image(logo_url, width=110)

st.markdown("<hr>", unsafe_allow_html=True)

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

if not st.session_state.logged_in:
    st.stop()

# =========================
# 7) تحميل البيانات الأساسية
# =========================
units = [r["name"] for r in (supabase.table("units_names").select("name").execute().data or [])]
plats = [r["name"] for r in (supabase.table("platforms").select("name").execute().data or [])]

today = date.today()

# =========================
# 8) التبويبات
# =========================
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

    bookings = supabase.table("bookings").select("*").execute().data or []

    occupied_units = [b["unit_no"] for b in bookings if b.get("unit_no") and b.get("check_out")]
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
            st.info("لا توجد وحدات شاغرة")

    with col2:
        st.markdown("### 🔴 الوحدات المشغولة")
        if occupied_units:
            for u in occupied_units:
                if st.button(f"إخلاء {u}", key=f"occ_{u}"):
                    supabase.table("bookings").delete().eq("unit_no", u).execute()
                    st.success(f"تم إخلاء الوحدة {u}")
                    st.experimental_rerun()
        else:
            st.info("لا توجد وحدات مشغولة")

# =========================================================
# ➕ التبويب الثاني: إضافة حجز جديد
# =========================================================
with tabs[1]:
    st.subheader("➕ إضافة حجز جديد")

    with st.form("new_booking"):
        unit = st.selectbox("الوحدة", units)
        platform = st.selectbox("المنصة", plats)
        guest = st.text_input("اسم العميل")
        phone = st.text_input("رقم الهاتف")
        check_in = st.date_input("الدخول", today)
        check_out = st.date_input("الخروج", today + timedelta(days=1))
        price = st.number_input("السعر", min_value=0)
        expenses = st.number_input("المصاريف", min_value=0)
        compensation = st.number_input("التعويضات", min_value=0)
        notes = st.text_area("ملاحظات")

        if st.form_submit_button("💾 حفظ"):
            supabase.table("bookings").insert({
                "unit_no": unit,
                "client_name": guest,
                "platform": platform,
                "phone": phone,
                "check_in": str(check_in),
                "check_out": str(check_out),
                "price": price,
                "expenses": expenses,
                "compensations": compensation,
                "note": notes
            }).execute()
            st.success("تمت إضافة الحجز")
            st.experimental_rerun()

# =========================================================
# 📋 التبويب الثالث: السجل العام
# =========================================================
with tabs[2]:
    st.subheader("📋 السجل العام")

    all_bookings = supabase.table("bookings").select("*").order("id", desc=True).execute().data or []

    search = st.text_input("🔍 بحث بالاسم أو الهاتف")

    if search:
        all_bookings = [
            b for b in all_bookings
            if search in b.get("client_name", "") or search in b.get("phone", "")
        ]

    st.markdown("### 🔔 حجوزات يقترب خروجها")

    near_exit = []
    for b in all_bookings:
        try:
            co = datetime.strptime(b["check_out"], "%Y-%m-%d").date()
            if co <= today + timedelta(days=1):
                near_exit.append(b)
        except:
            pass

    if near_exit:
        for b in near_exit:
            st.warning(f"الوحدة {b['unit_no']} — العميل {b['client_name']} — الخروج {b['check_out']}")
    else:
        st.info("لا توجد حجوزات قريبة الخروج")

    st.markdown("---")

    for b in all_bookings:
        with st.expander(f"📌 {b['unit_no']} — {b['client_name']}"):
            st.write(f"**الهاتف:** {b['phone']}")
            st.write(f"**المنصة:** {b['platform']}")
            st.write(f"**السعر:** {b['price']}")
            st.write(f"**المصاريف:** {b['expenses']}")
            st.write(f"**التعويضات:** {b['compensations']}")
            st.write(f"**ملاحظات:** {b['note']}")

            colA, colB, colC = st.columns(3)

            with colA:
                wa = f"https://wa.me/{b['phone']}?text=مرحباً {b['client_name']}"
                st.markdown(f"[📱 واتساب]({wa})")

            with colB:
                if st.button("✏️ تعديل", key=f"edit_{b['id']}"):
                    st.session_state.edit_booking = b
                    st.experimental_rerun()

            with colC:
                if st.button("🗑️ حذف", key=f"del_{b['id']}"):
                    supabase.table("bookings").delete().eq("id", b["id"]).execute()
                    st.error("تم حذف الحجز")
                    st.experimental_rerun()

    if st.session_state.edit_booking:
        edit = st.session_state.edit_booking
        st.markdown("## ✏️ تعديل الحجز")

        with st.form("edit_form"):
            unit = st.selectbox("الوحدة", units, index=units.index(edit["unit_no"]))
            guest = st.text_input("العميل", edit["client_name"])
            phone = st.text_input("الهاتف", edit["phone"])
            check_in = st.date_input("الدخول", datetime.strptime(edit["check_in"], "%Y-%m-%d"))
            check_out = st.date_input("الخروج", datetime.strptime(edit["check_out"], "%Y-%m-%d"))
            price = st.number_input("السعر", min_value=0, value=edit["price"])
            expenses = st.number_input("المصاريف", min_value=0, value=edit["expenses"])
            compensation = st.number_input("التعويضات", min_value=0, value=edit["compensations"])
            notes = st.text_area("ملاحظات", edit["note"])

            if st.form_submit_button("💾 حفظ"):
                supabase.table("bookings").update({
                    "unit_no": unit,
                    "client_name": guest,
                    "phone": phone,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "price": price,
                    "expenses": expenses,
                    "compensations": compensation,
                    "note": notes
                }).eq("id", edit["id"]).execute()

                st.success("تم التحديث")
                st.session_state.edit_booking = None
                st.experimental_rerun()

# =========================================================
# 💰 التبويب الرابع: التقارير المالية
# =========================================================
with tabs[3]:
    st.subheader("💰 التقارير المالية")

    fin = supabase.table("bookings").select("*").execute().data or []

    if not fin:
        st.info("لا توجد بيانات مالية")
    else:
        total_income = sum(b.get("price", 0) for b in fin)
        total_expenses = sum(b.get("expenses", 0) for b in fin)
        total_comp = sum(b.get("compensations", 0) for b in fin)
        net = total_income - total_expenses + total_comp

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 الدخل", total_income)
        col2.metric("💸 المصاريف", total_expenses)
        col3.metric("⚠️ التعويضات", total_comp)
        col4.metric("📈 الصافي", net)

        st.markdown("---")

        months = sorted(list(set(
            datetime.strptime(b["check_in"], "%Y-%m-%d").strftime("%Y-%m")
            for b in fin
        )))

        if months:
            selected = st.selectbox("اختر الشهر", months)
            month_data = [
                b for b in fin
                if datetime.strptime(b["check_in"], "%Y-%m-%d").strftime("%Y-%m") == selected
            ]

            if month_data:
                st.dataframe(pd.DataFrame(month_data))
            else:
                st.info("لا توجد بيانات لهذا الشهر")

# =========================================================
# ⚙️ التبويب الخامس: الإعدادات
# =========================================================
with tabs[4]:
    if st.session_state.user_role != "admin":
        st.error("❌ هذه الصفحة للمدير فقط")
    else:
        st.subheader("⚙️ إعدادات النظام")

        new_name = st.text_input("اسم البرنامج", value=app_name)
        if st.button("💾 حفظ الاسم"):
            supabase.table("settings").upsert({"key": "app_name", "value": new_name}).execute()
            st.success("تم تحديث الاسم")
            st.experimental_rerun()

        st.markdown("---")

        new_logo = st.text_input("رابط الشعار", value=logo_url)
        if st.button("💾 حفظ الشعار"):
            supabase.table("settings").upsert({"key": "logo_path", "value": new_logo}).execute()
            st.success("تم تحديث الشعار")
            st.experimental_rerun()

        st.markdown("---")

        bg_link = st.text_input("رابط الخلفية", value=background_image)
        if st.button("💾 حفظ الخلفية"):
            supabase.table("settings").upsert({"key": "background_image", "value": bg_link}).execute()
            st.success("تم تحديث الخلفية")
            st.experimental_rerun()

        if st.button("🗑️ إزالة الخلفية"):
            supabase.table("settings").upsert({"key": "background_image", "value": ""}).execute()
            st.success("تمت إزالة الخلفية")
            st.experimental_rerun()

        st.markdown("---")

        new_unit = st.text_input("إضافة وحدة جديدة")
        if st.button("➕ إضافة الوحدة"):
            if new_unit:
                supabase.table("units_names").insert({"name": new_unit}).execute()
                st.success("تمت الإضافة")
                st.experimental_rerun()
            else:
                st.error("أدخل اسم الوحدة")

        st.markdown("---")

        new_platform = st.text_input("إضافة منصة جديدة")
        if st.button("➕ إضافة المنصة"):
            if new_platform:
                supabase.table("platforms").insert({"name": new_platform}).execute()
                st.success("تمت الإضافة")
                st.experimental_rerun()
            else:
                st.error("أدخل اسم المنصة")

        st.markdown("---")

        new_user = st.text_input("اسم مستخدم جديد")
        new_pass = st.text_input("كلمة المرور", type="password")
        new_role = st.selectbox("الصلاحية", ["admin", "user"])

        if st.button("➕ إضافة المستخدم"):
            if new_user and new_pass:
                supabase.table("users").insert({
                    "username": new_user,
                    "password": new_pass,
                    "role": new_role
                }).execute()
                st.success("تمت الإضافة")
            else:
                st.error("أدخل جميع البيانات")

# =========================
# نهاية الملف
# =========================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; opacity:0.6;'>تم تطوير النظام باستخدام Streamlit + Supabase</p>",
    unsafe_allow_html=True
)

