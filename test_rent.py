import streamlit as st
import pandas as pd
from supabase import create_client
import os
from datetime import datetime, date

# --- إعدادات الاتصال السحابي (بياناتك الخاصة) ---
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_PSSSQPVdXIjYUXnaksqDNA_ikMQd1_-"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="نظام إدارة الوحدات السحابي", layout="wide")

# تهيئة الجلسة
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

# --- نظام تسجيل الدخول ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 دخول النظام")
    u = st.sidebar.text_input("اسم المستخدم")
    p = st.sidebar.text_input("كلمة المرور", type="password")
    if st.sidebar.button("دخول"):
        # التحقق من المستخدم في Supabase
        res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
        if res.data:
            st.session_state.update({'logged_in': True, 'user_name': u, 'user_role': res.data[0]['role']})
            st.rerun()
        else: st.sidebar.error("خطأ في بيانات الدخول")
else:
    st.sidebar.success(f"مرحباً: {st.session_state['user_name']}")
    tabs = st.tabs(["📊 حالة الوحدات", "➕ إضافة حجز", "📋 السجل العام", "⚙️ الإعدادات"])

    with tabs[0]: # حالة الوحدات
        st.header("🔍 الحالة اللحظية للوحدات")
        # جلب الوحدات والمنصات
        units = supabase.table("units_names").select("name").execute().data
        bookings = supabase.table("bookings").select("*").execute().data
        st.write("البيانات تعمل الآن سحابياً من أي جهاز!")

    if st.sidebar.button("تسجيل الخروج"):
        st.session_state['logged_in'] = False
        st.rerun()

