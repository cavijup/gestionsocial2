import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración básica
st.set_page_config(
    page_title="📊 Hub de Visualizaciones", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
/* Estilo principal */
.main-header {
    font-size: 2.5rem; 
    font-weight: bold; 
    color: #1565C0; 
    text-align: center; 
    margin-bottom: 2rem; 
    padding: 1.5rem; 
    background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%); 
    border-radius: 15px; 
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.dashboard-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    border-left: 5px solid #2196F3;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}

.dashboard-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.dashboard-title {
    font-size: 1.3rem;
    font-weight: bold;
    color: #2C3E50;
    margin-bottom: 0.5rem;
}

.dashboard-description {
    color: #7F8C8D;
    margin-bottom: 1rem;
    line-height: 1.6;
}

.dashboard-stats {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.stat-badge {
    background: #E8F5E8;
    color: #2E7D32;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
}

.sidebar-section {
    background: #F8F9FA;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
}

.success-message {
    background: #E8F5E8;
    color: #2E7D32;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    border-left: 4px solid #4CAF50;
}

.warning-message {
    background: #FFF3E0;
    color: #F57C00;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    border-left: 4px solid #FF9800;
}


</style>
""", unsafe_allow_html=True)



# Inicializar session state para los dashboards
if 'dashboards' not in st.session_state:
    st.session_state.dashboards = [
        {
            'id': 1,
            'titulo': 'Análisis por Sectores Institucionales',
            'descripcion': 'Cruce entre tipos de sector y categorías de actividades desarrolladas en comedores comunitarios.',
            'url': 'https://claude.ai/public/artifacts/50ac558e-63ae-4ddf-a264-b0d1ef8f89fe',
            'fecha_creacion': '2025-01-07',
            'tags': ['Sectores', 'Actividades', 'Comedores'],
            'activo': True
        },
        {
            'id': 2,
            'titulo': '🎭 Análisis: Temas vs Tipología del Comedor',
            'descripcion': 'Análisis cruzado entre los temas principales y la tipología de comedores comunitarios.',
            'url': 'https://claude.ai/public/artifacts/792db79b-4d09-49ad-ae0a-e353b2f3480c',
            'fecha_creacion': '2025-01-07',
            'tags': ['Temas', 'Tipología', 'Análisis Cruzado'],
            'activo': True
        },
        {
            'id': 3,
            'titulo': '🔗 Reconocimiento y Articulación',
            'descripcion': 'Dashboard de análisis sobre reconocimiento institucional y articulación entre diferentes actores del ecosistema de comedores comunitarios.',
            'url': 'https://claude.ai/public/artifacts/a7f6a48b-b3c7-40b3-bc9c-0b1fcb2b4ff2',
            'fecha_creacion': '2025-01-07',
            'tags': ['Reconocimiento', 'Articulación', 'Institucional'],
            'activo': True
        },
        {
            'id': 4,
            'titulo': '🍽️ Actividades Adicionales en Comedores',
            'descripcion': 'Análisis de las actividades complementarias y adicionales que se desarrollan en los comedores comunitarios más allá de la alimentación.',
            'url': 'https://claude.ai/public/artifacts/54a82b27-7c4f-4984-b5d8-e89f0ada15c3',
            'fecha_creacion': '2025-01-07',
            'tags': ['Actividades', 'Complementarias', 'Servicios'],
            'activo': True
        }
    ]

def add_dashboard(titulo, descripcion, url, tags):
    """Añade un nuevo dashboard a la lista"""
    new_dashboard = {
        'id': len(st.session_state.dashboards) + 1,
        'titulo': titulo,
        'descripcion': descripcion,
        'url': url,
        'fecha_creacion': datetime.now().strftime('%Y-%m-%d'),
        'tags': tags,
        'activo': True
    }
    st.session_state.dashboards.append(new_dashboard)

def main():
    # Header principal
    st.markdown('<div class="main-header">📊 Hub de Visualizaciones - Comedores Comunitarios</div>', unsafe_allow_html=True)
    
    # Sidebar para gestión
    with st.sidebar:
        st.markdown("## 🎛️ Panel de Control")
        
        # Estadísticas generales
        total_dashboards = len(st.session_state.dashboards)
        active_dashboards = len([d for d in st.session_state.dashboards if d['activo']])
        
        st.markdown(f"""
        <div class="sidebar-section">
            <h4>📈 Estadísticas</h4>
            <p><strong>Total:</strong> {total_dashboards} dashboards</p>
            <p><strong>Activos:</strong> {active_dashboards} dashboards</p>
            <p><strong>Última actualización:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sección para añadir nuevos dashboards
        st.markdown("## ➕ Añadir Dashboard")
        
        with st.expander("Nuevo Dashboard", expanded=False):
            with st.form("add_dashboard_form"):
                nuevo_titulo = st.text_input("Título del Dashboard")
                nueva_descripcion = st.text_area("Descripción", height=100)
                nueva_url = st.text_input("URL del Dashboard")
                nuevos_tags = st.text_input("Tags (separados por coma)", placeholder="tag1, tag2, tag3")
                
                submitted = st.form_submit_button("🚀 Añadir Dashboard")
                
                if submitted:
                    if nuevo_titulo and nueva_descripcion and nueva_url:
                        tags_list = [tag.strip() for tag in nuevos_tags.split(',') if tag.strip()]
                        add_dashboard(nuevo_titulo, nueva_descripcion, nueva_url, tags_list)
                        st.success("✅ Dashboard añadido exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Por favor, completa todos los campos obligatorios")
        
        # Filtros
        st.markdown("## 🔍 Filtros")
        
        # Filtro por tags
        all_tags = list(set([tag for dashboard in st.session_state.dashboards for tag in dashboard['tags']]))
        selected_tags = st.multiselect("Filtrar por tags:", all_tags)
        
        # Orden
        sort_order = st.selectbox("Ordenar por:", ["Más reciente", "Más antiguo", "Alfabético"])
    

    
    # Contenido principal - Lista de Dashboards
    st.markdown("## 📋 Lista de Dashboards")
    
    # Filtrar dashboards
    filtered_dashboards = st.session_state.dashboards.copy()
    
    if selected_tags:
        filtered_dashboards = [d for d in filtered_dashboards if any(tag in d['tags'] for tag in selected_tags)]
    
    # Ordenar dashboards
    if sort_order == "Más reciente":
        filtered_dashboards.sort(key=lambda x: x['fecha_creacion'], reverse=True)
    elif sort_order == "Más antiguo":
        filtered_dashboards.sort(key=lambda x: x['fecha_creacion'])
    elif sort_order == "Alfabético":
        filtered_dashboards.sort(key=lambda x: x['titulo'])
    
    # Mostrar dashboards (SIN botones de eliminar, ver, cambiar estado)
    if filtered_dashboards:
        for dashboard in filtered_dashboards:
            status_icon = "🟢" if dashboard['activo'] else "🔴"
            
            st.markdown(f"""
            <div class="dashboard-card">
                <div class="dashboard-title">{status_icon} {dashboard['titulo']}</div>
                <div class="dashboard-description">{dashboard['descripcion']}</div>
                <div class="dashboard-stats">
                    <span class="stat-badge">📅 {dashboard['fecha_creacion']}</span>
                    <span class="stat-badge">🏷️ {', '.join(dashboard['tags'])}</span>
                    <span class="stat-badge">🔗 <a href="{dashboard['url']}" target="_blank">Abrir Dashboard</a></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
    else:
        st.markdown("""
        <div class="warning-message">
            <h4>⚠️ No hay dashboards disponibles</h4>
            <p>No se encontraron dashboards que coincidan con los filtros seleccionados.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()