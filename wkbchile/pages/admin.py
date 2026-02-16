import streamlit as st
import pandas as pd
import hashlib
from utils.database import cargar_inscripciones, PRECIO_INSCRIPCION

def check_password():
    """Verifica la contraseña del admin"""
    
    def password_entered():
        """Verifica si la contraseña es correcta"""
        # Hash de la contraseña ingresada
        hashed = hashlib.sha256(st.session_state["password"].encode()).hexdigest()
        if hashed == st.secrets["general"]["admin_token_hash"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # No guardar la contraseña
        else:
            st.session_state["password_correct"] = False
    
    # Verificar si ya está autenticado
    if st.session_state.get("password_correct", False):
        return True
    
    # Mostrar formulario de login
    st.markdown("""
    <div style="text-align: center; margin: 50px 0;">
        <h3 style="color: #FDB931;">🔐 ACCESO RESTRINGIDO</h3>
        <p style="color: #9ca3af;">Ingresa la contraseña de administrador</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.text_input(
        "Contraseña", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state:
        if not st.session_state["password_correct"]:
            st.error("❌ Contraseña incorrecta")
    
    return False

def show():
    """Panel de administración"""
    
    st.markdown('<h2 class="title">⚙️ PANEL DE ADMINISTRACIÓN</h2>', unsafe_allow_html=True)
    
    # Breadcrumb
    st.markdown("""
    <div style="color: #9ca3af; margin-bottom: 20px;">
        🏠 Inicio > ⚙️ Administración
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar autenticación
    if not check_password():
        return
    
    # Cargar datos
    df = cargar_inscripciones()
    
    # Tabs para diferentes secciones
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Inscripciones", "⚙️ Configuración"])
    
    with tab1:
        st.markdown("### 📊 DASHBOARD")
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            confirmados = len(df[df['Estado_Pago'] == 'Confirmado'])
            pendientes = len(df[df['Estado_Pago'] != 'Confirmado'])
            
            with col1:
                st.metric("Total Inscripciones", len(df))
            with col2:
                st.metric("✅ Confirmados", confirmados)
            with col3:
                st.metric("⏳ Pendientes", pendientes)
            with col4:
                total = confirmados * PRECIO_INSCRIPCION
                st.metric("💰 Total", f"${total:,}")
            
            # Gráficos simples
            st.markdown("### 📈 Estadísticas por Categoría")
            categorias = df[df['Estado_Pago'] == 'Confirmado']['Categoria'].value_counts()
            st.bar_chart(categorias)
            
        else:
            st.info("No hay datos para mostrar")
    
    with tab2:
        st.markdown("### 📋 LISTA DE INSCRIPCIONES")
        
        if not df.empty:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                estado = st.selectbox("Filtrar por estado", ["Todos", "Confirmado", "Pendiente"])
            with col2:
                categoria = st.selectbox("Filtrar por categoría", ["Todas"] + CATEGORIAS)
            
            df_filtrado = df.copy()
            if estado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Estado_Pago'] == estado]
            if categoria != "Todas":
                df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria]
            
            st.dataframe(df_filtrado, use_container_width=True)
            
            # Exportar
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 DESCARGAR CSV",
                csv,
                f"inscripciones_wkb_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.info("No hay inscripciones aún")
    
    with tab3:
        st.markdown("### ⚙️ CONFIGURACIÓN")
        st.markdown("""
        <div class="card">
            <h4 style="color: #FDB931;">Próximamente</h4>
            <p style="color: #9ca3af;">- Configuración de precios</p>
            <p style="color: #9ca3af;">- Fechas del torneo</p>
            <p style="color: #9ca3af;">- Categorías personalizadas</p>
            <p style="color: #9ca3af;">- Exportación de datos</p>
        </div>
        """, unsafe_allow_html=True)