import streamlit as st
import pandas as pd
from utils.database import cargar_inscripciones
import datetime

def show():
    """Muestra el mural de competidores"""
    
    st.markdown('<h2 class="title">🥋 MURAL DE COMPETIDORES</h2>', unsafe_allow_html=True)
    
    # Breadcrumb
    st.markdown("""
    <div style="color: #9ca3af; margin-bottom: 20px;">
        🏠 Inicio > 👥 Mural de Competidores
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    df = cargar_inscripciones()
    
    if df.empty:
        st.info("📭 No hay inscritos aún. ¡Sé el primero en inscribirte!")
        if st.button("📝 INSCRIBIRME AHORA", use_container_width=True):
            st.query_params["page"] = "inscripciones"
            st.rerun()
        return
    
    # Filtrar solo confirmados
    df_confirmados = df[df['Estado_Pago'] == 'Confirmado'].copy()
    
    if df_confirmados.empty:
        st.info("⏳ No hay inscripciones confirmadas todavía.")
        return
    
    # Estadísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Inscritos", len(df_confirmados))
    with col2:
        st.metric("Categorías", len(df_confirmados['Categoria'].unique()))
    with col3:
        st.metric("Dojos", len(df_confirmados['Dojo'].unique()))
    with col4:
        from utils.database import PRECIO_INSCRIPCION
        total_recaudado = len(df_confirmados) * PRECIO_INSCRIPCION
        st.metric("Total Recaudado", f"${total_recaudado:,}")
    
    # Filtros
    with st.expander("🔍 FILTROS DE BÚSQUEDA", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            categorias_disponibles = ['Todas'] + sorted(df_confirmados['Categoria'].unique().tolist())
            categoria_seleccionada = st.selectbox("Categoría", categorias_disponibles)
        
        with col2:
            busqueda = st.text_input("Buscar por nombre", placeholder="Escribe un nombre...")
        
        # Ordenamiento
        ordenar_por = st.selectbox("Ordenar por", ["Nombre", "Dojo", "Categoría", "Fecha"])
    
    # Aplicar filtros
    df_filtrado = df_confirmados.copy()
    
    if categoria_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria_seleccionada]
    
    if busqueda:
        df_filtrado = df_filtrado[df_filtrado['Nombre_Completo'].str.contains(busqueda, case=False, na=False)]
    
    # Ordenar
    if ordenar_por == "Nombre":
        df_filtrado = df_filtrado.sort_values('Nombre_Completo')
    elif ordenar_por == "Dojo":
        df_filtrado = df_filtrado.sort_values('Dojo')
    elif ordenar_por == "Categoría":
        df_filtrado = df_filtrado.sort_values('Categoria')
    elif ordenar_por == "Fecha":
        df_filtrado = df_filtrado.sort_values('Fecha_Registro', ascending=False)
    
    # Mostrar resultados
    st.markdown(f"### 📋 Mostrando {len(df_filtrado)} competidores")
    
    # Vista en tarjetas (grid)
    cols = st.columns(3)
    for idx, (_, row) in enumerate(df_filtrado.iterrows()):
        with cols[idx % 3]:
            fecha = row.get('Fecha_Registro', '')
            if fecha and len(str(fecha)) > 10:
                fecha = str(fecha)[:10]
            else:
                fecha = 'Fecha no disponible'
            
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, #1f2937, #111827); 
                        border-radius: 12px; padding: 15px; margin: 10px 0;
                        border-left: 4px solid #FDB931;">
                <h4 style="color: #FDB931; margin: 0 0 10px 0;">{row['Nombre_Completo']}</h4>
                <p style="color: #e5e7eb; margin: 5px 0;">
                    <span style="color: #9ca3af;">🥋 Dojo:</span> {row.get('Dojo', 'N/A')}
                </p>
                <p style="color: #e5e7eb; margin: 5px 0;">
                    <span style="color: #9ca3af;">🏆 Categoría:</span> {row['Categoria']}
                </p>
                <p style="color: #e5e7eb; margin: 5px 0;">
                    <span style="color: #9ca3af;">📅 Fecha:</span> {fecha}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Vista en tabla (opcional)
    with st.expander("📊 VER COMO TABLA"):
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Descargar CSV
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 DESCARGAR LISTA (CSV)",
            csv,
            f"inscritos_wkb_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )