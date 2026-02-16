import streamlit as st
from streamlit_option_menu import option_menu
import pages.inicio as inicio
import pages.inscripciones as inscripciones
import pages.mural as mural
import pages.admin as admin
import pages.pago as pago

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="WKB Torneo Oficial",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Meta tags para móvil y SEO
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Sistema de inscripciones oficial del Torneo WKB Chile 2025">
<meta name="keywords" content="karate, WKB, torneo, inscripciones, artes marciales">
<title>WKB Chile - Torneo Oficial 2025</title>
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {
        background: linear-gradient(135deg, #0e1117 0%, #1a1f2e 100%);
    }
    /* Estilos globales */
    .title {
        color: #FDB931;
        font-size: 32px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .card {
        background: #1f2937;
        border-radius: 15px;
        padding: 25px;
        border: 1px solid #374151;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    /* Header con logo */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background: linear-gradient(180deg, #1f2937 0%, #0e1117 100%);
        border-bottom: 1px solid #374151;
        margin-bottom: 20px;
    }
    .logo-text {
        color: #FDB931;
        font-weight: bold;
        font-size: 20px;
    }
    @media (max-width: 768px) {
        .title { font-size: 24px; }
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER COMÚN ---
def render_header():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-PCwsXVnqhlX-vNev8BDqbszitBpm3cC8GQ&s" 
                 style="height: 60px; margin-bottom: 10px;">
            <h1 style="color: #FDB931; margin: 0; font-size: 24px;">WKB CHILE</h1>
            <p style="color: #9ca3af; margin: 0;">TORNEO OFICIAL 2025</p>
        </div>
        """, unsafe_allow_html=True)

# --- SISTEMA DE RUTAS / URLS ---
def get_current_page():
    """Obtiene la página actual basada en la URL"""
    query_params = st.query_params
    return query_params.get("page", ["inicio"])[0]

def set_page(page):
    """Cambia la página actual actualizando la URL"""
    st.query_params["page"] = page
    st.rerun()

# --- MENÚ DE NAVEGACIÓN ---
def render_navigation():
    """Renderiza el menú de navegación con st.query_params"""
    
    current_page = get_current_page()
    
    # Mapeo de páginas a nombres amigables
    pages_map = {
        "inicio": "🏠 Inicio",
        "inscripciones": "📝 Inscripciones",
        "mural": "👥 Mural",
        "admin": "⚙️ Admin"
    }
    
    # Crear menú horizontal con columnas
    cols = st.columns(len(pages_map))
    
    for i, (page_key, page_name) in enumerate(pages_map.items()):
        with cols[i]:
            # Estilo diferente para la página activa
            if current_page == page_key:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; 
                            background: rgba(253, 185, 49, 0.2); 
                            border-radius: 10px;
                            border: 1px solid #FDB931;">
                    <span style="color: #FDB931; font-weight: bold;">{page_name}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                    set_page(page_key)
    
    st.markdown("---")

# --- FUNCIÓN PRINCIPAL ---
def main():
    """Función principal con enrutamiento"""
    
    # Renderizar header común
    render_header()
    
    # Renderizar navegación
    render_navigation()
    
    # Obtener página actual
    current_page = get_current_page()
    
    # Enrutamiento
    if current_page == "inicio":
        import pages.inicio as inicio
        inicio.show()
    elif current_page == "inscripciones":
        import pages.inscripciones as inscripciones
        inscripciones.show()
    elif current_page == "mural":
        import pages.mural as mural
        mural.show()
    elif current_page == "admin":
        import pages.admin as admin
        admin.show()
    elif current_page == "pago":
        import pages.pago as pago
        pago.show()
    else:
        # Página no encontrada, redirigir a inicio
        set_page("inicio")

if __name__ == "__main__":
    main()