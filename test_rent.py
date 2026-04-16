import streamlit as st
import pandas as pd
from supabase import create_client
import os
from datetime import datetime, date

# --- 1. إعدادات الاتصال السحابي ---
# ملاحظة: يجب وضع الرابط الكامل الخاص بك هنا
URL = "https://sdoeyobzknoycovobbvc.supabase.co" 
KEY = "sb_publishable_PSSSQPVdXIjYUXnaksqDNA_ikMQd1_-"
supabase = create_client(URL, KEY)

# --- 2. تهيئة الجلسة ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'user_role' not in st.session_state: st.session_state.user_role = ""
if 'selected_unit' not in st.session_state: st.session_state.selected_unit = None

# --- 3. تحسين الواجهة باستخدام CSS ---
st.set_page_config(page_title="نظام الإدارة السحابي", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: #007bff; color: white; font-weight: bold; border: none;
    }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 4. نظام تسجيل الدخول ---
if not st.session_state.logged_in:
    st.sidebar.title("🔐 تسجيل الدخول")
    with st.sidebar.form("login_form"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            # تصحيح: التحقق من وجود بيانات (res.data) قبل محاولة القراءة
            if res.data and len(res.data) > 0:
                st.session_state.update({
                    'logged_in': True, 
                    'user_name': u, 
                    'user_role': res.data[0]['role'] # تعديل: استخراج الدور من أول صف متاح
                })
                st.rerun()
            else: st.sidebar.error("❌ بيانات خاطئة")
else:
    st.sidebar.success(f"👤 {st.session_state.user_name} ({st.session_state.user_role})")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    # جلب البيانات الأساسية (تأكد من وجود الجداول في Supabase)
    today = date.today()
    
    # تصحيح: التأكد من جلب البيانات بشكل سليم
    units_res = supabase.table("units_names").select("name").execute()
    all_units = [r['name'] for r in units_res.data] if units_res.data else []
    
    plats_res = supabase.table("platforms").select("name").execute()
    all_plats = [r['name'] for r in plats_res.data] if plats_res.data else []
    
    # --- 5. التبويبات الرئيسية ---
    tabs = st.tabs(["📊 حالة الوحدات", "➕ إضافة حجز", "📋 السجل العام", "💰 المالية والتقارير", "⚙️ الإعدادات"])

    # تبويب 1: حالة الوحدات
    with tabs[0]:
        st.subheader("🔍 مراقبة الإشغال اللحظي")
        occ_res = supabase.table("bookings").select("*").lte("check_in", str(today)).gt("check_out", str(today)).execute().data
        occ_names = [r['unit_no'] for r in occ_res] if occ_res else []
        
        col_occ, col_vac = st.columns(2)
        with col_occ:
            st.markdown("#### 🔴 مشغولة الآن")
            if occ_res:
                for r in occ_res:
                    c1, c2 = st.columns([3, 1])
                    c1.error(f"🏠 {r['unit_no']} - {r['client_name']}")
                    if c2.button("إخلاء", key=f"end_{r['id']}"):
                        supabase.table("bookings").update({"check_out": str(today)}).eq("id", r['id']).execute()
                        st.rerun()
            else: st.info("لا توجد وحدات مشغولة")
            
        with col_vac:
            st.markdown("#### 🟢 متاحة للحجز")
            vacant_units = [un for un in all_units if un not in occ_names]
            if vacant_units:
                for u in vacant_units:
                    c1, c2 = st.columns([3, 1])
                    c1.success(f"🔑 {u}")
                    if c2.button("حجز", key=f"bk_{u}"):
                        st.session_state.selected_unit = u
                        # تعديل: التنقل لتبويب الحجز برمجياً غير مدعوم بسهولة في التبويبات ولكن سيتم اختيار الوحدة
                        st.rerun()
            else: st.warning("جميع الوحدات مشغولة")

    # تبويب 2: إضافة حجز
    with tabs[1]:
        st.subheader("📝 تسجيل حجز جديد")
        if all_units:
            idx = all_units.index(st.session_state.selected_unit) if st.session_state.selected_unit in all_units else 0
            with st.form("add_booking", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    u_sel = st.selectbox("الوحدة", all_units, index=idx)
                    p_sel = st.selectbox("المنصة", all_plats) if all_plats else st.info("أضف منصات أولاً")
                    c_name = st.text_input("اسم العميل")
                    c_phone = st.text_input("رقم الهاتف")
                with col2:
                    price = st.number_input("السعر", min_value=0.0)
                    d_in = st.date_input("الدخول", value=today)
                    d_out = st.date_input("الخروج")
                    exp = st.number_input("مصروفات", min_value=0.0)
                    comp = st.number_input("تعويضات", min_value=0.0)
                if st.form_submit_button("✅ حفظ في السحابة"):
                    data = {"unit_no": u_sel, "client_name": c_name, "phone": c_phone, "platform": p_sel, "price": price, 
                            "check_in": str(d_in), "check_out": str(d_out), "expenses": exp, "compensations": comp, "added_by": st.session_state.user_name}
                    supabase.table("bookings").insert(data).execute()
                    st.session_state.selected_unit = None
                    st.success("تم الحفظ بنجاح!")
                    st.rerun()
        else: st.warning("يرجى إضافة وحدات أولاً من تبويب الإعدادات")

    # تبويب 3: السجل العام
    with tabs[2]:
        bookings_data = supabase.table("bookings").select("*").execute().data
        df = pd.DataFrame(bookings_data) if bookings_data else pd.DataFrame()
        if not df.empty:
            st.dataframe(df[['unit_no', 'client_name', 'phone', 'platform', 'check_in', 'added_by']], use_container_width=True)

    # تبويب 4: المالية
    with tabs[3]:
        if st.session_state.user_role == "مدير" and not df.empty:
            df['الصافي'] = df['price'] + df['compensations'] - df['expenses']
            m1, m2, m3 = st.columns(3)
            m1.metric("إجمالي الدخل", f"{df['price'].sum()} ريال")
            m2.metric("إجمالي المصاريف", f"{df['expenses'].sum()} ريال")
            m3.metric("صافي الربح", f"{df['الصافي'].sum()} ريال")
            st.dataframe(df, use_container_width=True)

    # تبويب 5: الإعدادات
    with tabs[4]:
        if st.session_state.user_role == "مدير":
            st.subheader("⚙️ إدارة النظام")
            col_u, col_m = st.columns(2)
            with col_u:
                nu = st.text_input("اسم وحدة جديدة")
                if st.button("حفظ الوحدة"):
                    supabase.table("units_names").insert({"name": nu}).execute()
                    st.rerun()
            with col_m:
                mu, mp = st.text_input("موظف جديد"), st.text_input("كلمة سر")
                if st.button("إضافة موظف"):
                    supabase.table("users").insert({"username": mu, "password": mp, "role": "موظف"}).execute()
                    st.success(f"تمت إضافة {mu}")


