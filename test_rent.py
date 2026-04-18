import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime, timedelta
import base64
import io
import plotly.express as px

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
        "logged_logged": False,
        "user_name": "",
        "user_role": "",
        "selected_unit": None,
        "edit_booking": None,
        "edit_financial": None
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
# 4) الخلفية + ثيم Glass UI
# =========================
glass_css = """
<style>
.stApp {
    background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #020617 100%);
    color: #e5e7eb;
}
.block-container {
    padding: 2.5rem 2.5rem 3rem 2.5rem;
}
.glass-card {
    background: rgba(15, 23, 42, 0.65);
    border-radius: 18px;
    border: 1px solid rgba(148, 163, 184, 0.35);
    box-shadow: 0 18px 45px rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(18px);
    padding: 1.4rem 1.6rem;
}
.glass-metric {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(8, 47, 73, 0.75));
    border-radius: 16px;
    border: 1px solid rgba(59, 130, 246, 0.55);
    box-shadow: 0 18px 40px rgba(37, 99, 235, 0.55);
    backdrop-filter: blur(16px);
    padding: 1.2rem 1.4rem;
}
.neon-title {
    font-size: 1.4rem;
    font-weight: 700;
    background: linear-gradient(90deg, #60a5fa, #22d3ee);
    -webkit-background-clip: text;
    color: transparent;
}
.neon-sub {
    font-size: 0.9rem;
    color: #9ca3af;
}
.neon-number {
    font-size: 1.8rem;
    font-weight: 800;
    color: #e5e7eb;
}
.neon-pill {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    border: 1px solid rgba(96, 165, 250, 0.7);
    color: #bfdbfe;
}
hr {
    border-color: rgba(55, 65, 81, 0.7);
}
</style>
"""

st.markdown(glass_css, unsafe_allow_html=True)

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
        f"""
        <div style='text-align:center; margin-bottom:0.5rem;'>
            <div style="font-size:2.1rem; font-weight:800; 
                        background:linear-gradient(90deg,#60a5fa,#22d3ee);
                        -webkit-background-clip:text; color:transparent;">
                {app_name}
            </div>
            <div style="font-size:0.9rem; color:#9ca3af;">
                نظام إدارة حجوزات الوحدات العقارية — واجهة فاخرة (Glass UI)
            </div>
        </div>
        """,
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
                st.rerun()
            else:
                st.sidebar.error("❌ بيانات خاطئة")
else:
    st.sidebar.success(f"👤 {st.session_state.user_name} ({st.session_state.user_role})")

    if st.sidebar.button("🚪 خروج"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.logged_in = False
        st.rerun()

if not st.session_state.logged_in:
    st.stop()

# =========================
# 7) تحميل البيانات الأساسية
# =========================
units = [r["name"] for r in (supabase.table("units_names").select("name").execute().data or [])]
plats = [r["name"] for r in (supabase.table("platforms").select("name").execute().data or [])]

today = date.today()

# =========================
# 8) تبويبات النظام
# =========================
tabs = st.tabs([
    "🏠 الرئيسية",
    "📊 حالة الوحدات",
    "➕ حجز جديد",
    "📋 السجل العام",
    "💰 التقارير المالية",
    "⚙️ الإعدادات"
])
# =========================================================
# 📊 التبويب الثاني: حالة الوحدات
# =========================================================
with tabs[1]:
    st.markdown("<div class='neon-title'>حالة الوحدات الآن</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='neon-sub'>عرض سريع لحالة كل وحدة: مشغولة أو شاغرة، مع تفاصيل آخر حجز.</div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        selected_platform = st.selectbox("تصفية حسب المنصة", ["الكل"] + plats)
    with col_filter2:
        show_only_busy = st.checkbox("عرض الوحدات المشغولة فقط")

    # جلب آخر حجز لكل وحدة
    data = supabase.table("bookings").select("*").order("check_in", desc=True).execute().data or []
    last_by_unit = {}
    for b in data:
        u = b.get("unit_no")
        if not u:
            continue
        if u not in last_by_unit:
            last_by_unit[u] = b

    cards_cols = st.columns(4)

    for idx, u in enumerate(units):
        col = cards_cols[idx % 4]
        with col:
            b = last_by_unit.get(u)
            if b:
                busy = True if b.get("check_out") and b["check_out"] >= str(today) else False
            else:
                busy = False

            if show_only_busy and not busy:
                continue

            if selected_platform != "الكل" and b and b.get("platform") != selected_platform:
                continue

            bg = "linear-gradient(135deg, rgba(248,113,113,0.18), rgba(127,29,29,0.75))" if busy else \
                 "linear-gradient(135deg, rgba(34,197,94,0.18), rgba(6,78,59,0.75))"

            st.markdown(
                f"""
                <div class='glass-card' style="margin-bottom:0.9rem; background:{bg};">
                    <div style="font-size:1rem; font-weight:700; color:#e5e7eb;">الوحدة {u}</div>
                    <div style="font-size:0.8rem; color:#e5e7eb;">
                        الحالة: {"مشغولة" if busy else "شاغرة"}
                    </div>
                """,
                unsafe_allow_html=True
            )

            if b:
                st.markdown(
                    f"""
                    <div style="font-size:0.75rem; color:#e5e7eb; margin-top:0.3rem;">
                        العميل: {b.get('client_name','-')}<br>
                        من: {b.get('check_in','-')} — إلى: {b.get('check_out','-')}<br>
                        المنصة: {b.get('platform','-')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div style='font-size:0.75rem; color:#9ca3af; margin-top:0.3rem;'>لا يوجد حجز مسجل لهذه الوحدة.</div>",
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ➕ التبويب الثالث: حجز جديد
# =========================================================
with tabs[2]:
    st.markdown("<div class='neon-title'>إضافة حجز جديد</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='neon-sub'>تسجيل حجز جديد مع جميع التفاصيل المالية والإدارية.</div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("new_booking_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            unit_no = st.selectbox("الوحدة", units)
            platform = st.selectbox("المنصة", plats)
            client_name = st.text_input("اسم العميل")
        with c2:
            phone = st.text_input("رقم الجوال")
            check_in = st.date_input("تاريخ الدخول", value=today)
            check_out = st.date_input("تاريخ الخروج", value=today + timedelta(days=1))
        with c3:
            price = st.number_input("السعر الكلي", min_value=0, value=0)
            expenses = st.number_input("المصاريف", min_value=0, value=0)
            compensations = st.number_input("التعويضات", min_value=0, value=0)

        note = st.text_area("ملاحظات إضافية")

        submitted = st.form_submit_button("💾 حفظ الحجز")
        if submitted:
            if check_out < check_in:
                st.error("❌ تاريخ الخروج يجب أن يكون بعد تاريخ الدخول.")
            else:
                supabase.table("bookings").insert({
                    "unit_no": unit_no,
                    "platform": platform,
                    "client_name": client_name,
                    "phone": phone,
                    "check_in": str(check_in),
                    "check_out": str(check_out),
                    "price": price,
                    "expenses": expenses,
                    "compensations": compensations,
                    "note": note
                }).execute()
                st.success("✅ تم حفظ الحجز بنجاح.")

# =========================================================
# 📋 التبويب الرابع: السجل العام
# =========================================================
with tabs[3]:
    st.markdown("<div class='neon-title'>السجل العام للحجوزات</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='neon-sub'>عرض وتصفية جميع الحجوزات مع إمكانية التعديل والحذف.</div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    all_bookings = supabase.table("bookings").select("*").order("check_in", desc=True).execute().data or []

    f1, f2, f3 = st.columns(3)
    with f1:
        filter_unit = st.selectbox("تصفية حسب الوحدة", ["الكل"] + units)
    with f2:
        filter_platform = st.selectbox("تصفية حسب المنصة", ["الكل"] + plats)
    with f3:
        filter_client = st.text_input("بحث باسم العميل")

    filtered = []
    for b in all_bookings:
        if filter_unit != "الكل" and b.get("unit_no") != filter_unit:
            continue
        if filter_platform != "الكل" and b.get("platform") != filter_platform:
            continue
        if filter_client and filter_client not in (b.get("client_name") or ""):
            continue
        filtered.append(b)

    st.markdown(f"<div class='neon-sub'>عدد الحجوزات: {len(filtered)}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    for b in filtered:
        with st.expander(f"🧾 حجز رقم {b['id']} — الوحدة {b['unit_no']} — {b['client_name']}"):
            st.write(f"**الوحدة:** {b['unit_no']}")
            st.write(f"**المنصة:** {b['platform']}")
            st.write(f"**العميل:** {b['client_name']}")
            st.write(f"**الجوال:** {b['phone']}")
            st.write(f"**الدخول:** {b['check_in']}")
            st.write(f"**الخروج:** {b['check_out']}")
            st.write(f"**السعر:** {b['price']}")
            st.write(f"**المصاريف:** {b['expenses']}")
            st.write(f"**التعويضات:** {b['compensations']}")
            st.write(f"**ملاحظات:** {b['note']}")

            c1, c2, c3 = st.columns(3)

            # زر تعديل الحجز
            with c1:
                if st.button(f"✏️ تعديل الحجز {b['id']}", key=f"edit_booking_{b['id']}"):
                    st.session_state.edit_booking = b
                    st.rerun()

            # زر حذف الحجز
            with c2:
                if st.button(f"🗑️ حذف الحجز {b['id']}", key=f"del_booking_{b['id']}"):
                    supabase.table("bookings").delete().eq("id", b["id"]).execute()
                    st.error("تم حذف الحجز.")
                    st.rerun()

            # زر طباعة فاتورة PDF (يُفعل في التقارير المالية)
            with c3:
                st.info("🧾 طباعة الفاتورة متاحة من التقارير المالية.")

    # نافذة تعديل الحجز
    if st.session_state.edit_booking:
        b = st.session_state.edit_booking
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div class='neon-title'>تعديل الحجز</div>", unsafe_allow_html=True)

        with st.form("edit_booking_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                unit_no = st.selectbox("الوحدة", units, index=units.index(b["unit_no"]))
                platform = st.selectbox("المنصة", plats, index=plats.index(b["platform"]))
                client_name = st.text_input("اسم العميل", b["client_name"])
            with c2:
                phone = st.text_input("رقم الجوال", b["phone"])
                check_in = st.date_input("تاريخ الدخول", value=datetime.strptime(b["check_in"], "%Y-%m-%d").date())
                check_out = st.date_input("تاريخ الخروج", value=datetime.strptime(b["check_out"], "%Y-%m-%d").date())
            with c3:
                price = st.number_input("السعر الكلي", min_value=0, value=b["price"])
                expenses = st.number_input("المصاريف", min_value=0, value=b["expenses"])
                compensations = st.number_input("التعويضات", min_value=0, value=b["compensations"])

            note = st.text_area("ملاحظات إضافية", b["note"])

            if st.form_submit_button("💾 حفظ التعديلات"):
                if check_out < check_in:
                    st.error("❌ تاريخ الخروج يجب أن يكون بعد تاريخ الدخول.")
                else:
                    supabase.table("bookings").update({
                        "unit_no": unit_no,
                        "platform": platform,
                        "client_name": client_name,
                        "phone": phone,
                        "check_in": str(check_in),
                        "check_out": str(check_out),
                        "price": price,
                        "expenses": expenses,
                        "compensations": compensations,
                        "note": note
                    }).eq("id", b["id"]).execute()

                    st.success("تم تحديث الإعدادات، يرجى إعادة تحميل الصفحة.")

                    from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# =========================================================
# 🧾 دالة إنشاء فاتورة PDF A4 (عربي + إنجليزي)
# =========================================================
def generate_invoice_pdf(booking, settings):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    app_name = settings.get("app_name", "نظام إدارة الوحدات")

    y = height - 40 * mm

    # عنوان الفاتورة
    c.setFont("Helvetica-Bold", 18)
    c.drawString(30 * mm, y, "Invoice / فاتورة")
    y -= 10 * mm

    # اسم النظام
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30 * mm, y, app_name)
    y -= 8 * mm

    # بيانات عامة
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, f"Booking ID: {booking['id']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Client / العميل: {booking['client_name']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Unit / الوحدة: {booking['unit_no']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Platform / المنصة: {booking['platform']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Phone / الجوال: {booking['phone']}")
    y -= 10 * mm

    # تواريخ
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "Dates / التواريخ")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, f"Check-in / الدخول: {booking['check_in']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Check-out / الخروج: {booking['check_out']}")
    y -= 10 * mm

    # جدول مالي
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "Financial Details / التفاصيل المالية")
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, f"Price / السعر: {booking['price']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Expenses / المصاريف: {booking['expenses']}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"Compensations / التعويضات: {booking['compensations']}")
    y -= 6 * mm

    net = booking["price"] - booking["expenses"] + booking["compensations"]
    y -= 4 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, f"Net / الصافي: {net}")
    y -= 10 * mm

    # ملاحظات
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "Notes / الملاحظات:")
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    note = booking.get("note") or ""
    for line in note.split("\n"):
        c.drawString(30 * mm, y, line[:90])
        y -= 5 * mm
        if y < 30 * mm:
            break

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# =========================================================
# 💰 التبويب الخامس: التقارير المالية
# =========================================================
with tabs[4]:
    st.markdown("<div class='neon-title'>التقارير المالية</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='neon-sub'>تحليل الإيرادات والمصاريف والتعويضات مع إمكانية التعديل والحذف وطباعة الفواتير.</div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    all_fin = supabase.table("bookings").select("*").order("check_in", desc=True).execute().data or []

    c1, c2, c3 = st.columns(3)
    with c1:
        start_date = st.date_input("من تاريخ", value=today.replace(day=1))
    with c2:
        end_date = st.date_input("إلى تاريخ", value=today)
    with c3:
        fin_unit = st.selectbox("تصفية حسب الوحدة", ["الكل"] + units)

    fin = []
    for b in all_fin:
        try:
            d = datetime.strptime(b["check_in"], "%Y-%m-%d").date()
        except:
            continue
        if d < start_date or d > end_date:
            continue
        if fin_unit != "الكل" and b.get("unit_no") != fin_unit:
            continue
        fin.append(b)

    st.markdown(f"<div class='neon-sub'>عدد العمليات المالية: {len(fin)}</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    if fin:
        df_fin = pd.DataFrame(fin)
        total_income = df_fin["price"].sum()
        total_expenses = df_fin["expenses"].sum()
        total_comp = df_fin["compensations"].sum()
        net = total_income - total_expenses + total_comp

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("<div class='glass-metric'><div class='neon-sub'>إجمالي الإيرادات</div>"
                        f"<div class='neon-number'>{total_income}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='glass-metric'><div class='neon-sub'>إجمالي المصاريف</div>"
                        f"<div class='neon-number'>{total_expenses}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='glass-metric'><div class='neon-sub'>إجمالي التعويضات</div>"
                        f"<div class='neon-number'>{total_comp}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown("<div class='glass-metric'><div class='neon-sub'>صافي الربح</div>"
                        f"<div class='neon-number'>{net}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.dataframe(
            df_fin[["id", "unit_no", "client_name", "check_in", "check_out", "price", "expenses", "compensations"]],
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("لا توجد بيانات مالية ضمن الفترة المحددة.")

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # 🧾 فواتير PDF لكل عملية
    # =========================
    st.markdown("## 🧾 طباعة الفواتير (PDF A4 عربي + إنجليزي)")
    for b in fin:
        with st.expander(f"فاتورة الحجز رقم {b['id']} — {b['client_name']} — الوحدة {b['unit_no']}"):
            pdf_bytes = generate_invoice_pdf(b, settings)
            file_name = f"invoice_{b['id']}.pdf"
            st.download_button(
                label="📥 تحميل الفاتورة PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                key=f"pdf_{b['id']}"
            )

    # =========================
    # ✏️ تعديل / حذف العمليات المالية
    # =========================
    st.markdown("## ✏️ تعديل أو حذف العمليات المالية")

    for b in fin:
        with st.expander(f"🧾 العملية رقم {b['id']} — {b['client_name']} — {b['unit_no']}"):
            st.write(f"**الوحدة:** {b['unit_no']}")
            st.write(f"**العميل:** {b['client_name']}")
            st.write(f"**الدخول:** {b['check_in']}")
            st.write(f"**الخروج:** {b['check_out']}")
            st.write(f"**السعر:** {b['price']}")
            st.write(f"**المصاريف:** {b['expenses']}")
            st.write(f"**التعويضات:** {b['compensations']}")
            st.write(f"**ملاحظات:** {b['note']}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"✏️ تعديل العملية {b['id']}", key=f"edit_fin_{b['id']}"):
                    st.session_state.edit_financial = b
                    st.rerun()

            with col2:
                if st.button(f"🗑️ حذف العملية {b['id']}", key=f"del_fin_{b['id']}"):
                    supabase.table("bookings").delete().eq("id", b["id"]).execute()
                    st.error("تم حذف العملية المالية")
                    st.rerun()

    if st.session_state.edit_financial:
        b = st.session_state.edit_financial
        st.markdown("## ✏️ تعديل العملية المالية")

        with st.form("edit_fin_form"):
            price = st.number_input("السعر", min_value=0, value=b["price"])
            expenses = st.number_input("المصاريف", min_value=0, value=b["expenses"])
            comp = st.number_input("التعويضات", min_value=0, value=b["compensations"])
            note = st.text_area("ملاحظات", b["note"])

            if st.form_submit_button("💾 حفظ التعديلات"):
                supabase.table("bookings").update({
                    "price": price,
                    "expenses": expenses,
                    "compensations": comp,
                    "note": note
                }).eq("id", b["id"]).execute()

                st.success("تم تحديث العملية المالية")
                st.session_state.edit_financial = None
                st.rerun()

# =========================================================
# ⚙️ التبويب السادس: الإعدادات
# =========================================================
with tabs[5]:
    st.markdown("<div class='neon-title'>الإعدادات العامة للنظام</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='neon-sub'>تعديل اسم النظام، الشعار، الخلفية، وبعض الإعدادات العامة.</div>",
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.user_role != "admin":
        st.warning("هذه الصفحة متاحة للمدير فقط.")
    else:
        with st.form("settings_form"):
            app_name_in = st.text_input("اسم النظام", value=settings.get("app_name", "نظام إدارة الوحدات"))
            logo_in = st.text_input("رابط الشعار (logo_url)", value=settings.get("logo_path", ""))
            bg_in = st.text_input("رابط صورة الخلفية (اختياري)", value=settings.get("background_image", ""))

            if st.form_submit_button("💾 حفظ الإعدادات"):
                def upsert_setting(k, v):
                    supabase.table("settings").upsert({"key": k, "value": v}).execute()

                upsert_setting("app_name", app_name_in)
                upsert_setting("logo_path", logo_in)
                upsert_setting("background_image", bg_in)

                st.success("✅ تم تحديث الإعدادات، يرجى إعادة تحميل الصفحة.")

