import streamlit as st

def show():
    """Página de inicio"""
    
    st.markdown('<h2 class="title">BIENVENIDOS AL TORNEO WKB 2025</h2>', unsafe_allow_html=True)
    
    # Hero section
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="color: #FDB931;">🏆 TORNEO NACIONAL DE KARATE</h3>
            <p style="color: #e5e7eb; font-size: 16px; line-height: 1.6;">
                El evento más importante de karate en Chile. Más de 200 competidores 
                de todo el país se darán cita para competir en las diferentes categorías.
            </p>
            <ul style="color: #e5e7eb; list-style-type: none; padding: 0;">
                <li style="margin: 10px 0;">📍 <strong>Lugar:</strong> Gimnasio Polideportivo, Santiago</li>
                <li style="margin: 10px 0;">📅 <strong>Fecha:</strong> 15-16 Marzo 2025</li>
                <li style="margin: 10px 0;">⏰ <strong>Pesaje:</strong> 08:00 hrs</li>
                <li style="margin: 10px 0;">🥋 <strong>Competencia:</strong> 10:00 hrs</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h3 style="color: #FDB931;">📊 ESTADÍSTICAS</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Aquí podrías cargar estadísticas reales
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Inscritos", "150+", "↑12")
            st.metric("Categorías", "10", "→")
        with col_b:
            st.metric("Dojos", "25+", "↑5")
            st.metric("Premios", "$2M", "→")
    
    # Categorías destacadas
    st.markdown("### 🥋 CATEGORÍAS DESTACADAS")
    cols = st.columns(3)
    categorias = [
        ("KUMITE -65kg", "18+ Masculino"),
        ("KUMITE -55kg", "18+ Femenino"),
        ("KATA", "Mixto 18+")
    ]
    
    for i, (titulo, subtitulo) in enumerate(categorias):
        with cols[i]:
            st.markdown(f"""
            <div style="background: #1f2937; padding: 15px; border-radius: 10px; 
                        border-left: 3px solid #FDB931; margin: 10px 0;">
                <h4 style="color: #FDB931; margin: 0;">{titulo}</h4>
                <p style="color: #9ca3af; margin: 0;">{subtitulo}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Botones de acción
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("📝 INSCRIBIRSE AHORA", type="primary", use_container_width=True):
            st.query_params["page"] = "inscripciones"
            st.rerun()
            