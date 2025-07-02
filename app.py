import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Agregar rutas locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos locales
try:
    from utils.google_sheets import load_data_from_sheets, validate_connection
    from utils.data_analysis import analyze_tipo_comedor
    from config.settings import APP_TITLE
    modules_loaded = True
except ImportError:
    # Fallback si no existen los módulos (para compatibilidad)
    st.error("⚠️ Módulos locales no encontrados. Usando configuración básica.")
    APP_TITLE = "Dashboard Comedores Comunitarios"
    modules_loaded = False

# Configuración de la página
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E7D32;
    }
    .filter-header {
        color: #1976D2;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .status-indicator {
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-connected {
        background-color: #E8F5E8;
        color: #2E7D32;
    }
    .status-error {
        background-color: #FFEBEE;
        color: #C62828;
    }
</style>
""", unsafe_allow_html=True)

# Función para cargar datos usando Streamlit Secrets
@st.cache_data(ttl=300)
def load_data_secure():
    """Carga datos usando configuración segura desde Streamlit Secrets"""
    try:
        # Verificar si existen los secrets
        if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
            st.error("❌ Credenciales no configuradas. Configura los secrets en Streamlit Cloud.")
            return None
        
        # Importar dependencias
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Obtener credenciales desde secrets
        credentials_info = dict(st.secrets["gcp_service_account"])
        
        # Definir el scope
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Crear credenciales
        credentials = Credentials.from_service_account_info(credentials_info, scopes=scope)
        
        # Autorizar el cliente
        gc = gspread.authorize(credentials)
        
        # Obtener configuración de Google Sheets
        sheet_id = st.secrets.get("google_sheets", {}).get("sheet_id", "1fbs-J474JbvV3USg5aQlLUW9sNqkBjcd63qBU1nJeeI")
        worksheet_name = st.secrets.get("google_sheets", {}).get("worksheet_name", "Respuestas de formulario 1")
        
        # Abrir la hoja de cálculo
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Obtener todos los datos
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Limpiar datos básicos
        df = clean_dataframe(df)
        
        return df
        
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None

def clean_dataframe(df):
    """Limpia y prepara el DataFrame"""
    try:
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Convertir columnas numéricas donde sea posible
        numeric_columns = ['COMUNA', 'NODO ', 'NICHO ', 'AÑO DE VINCULACIÓN AL PROGRAMA']
        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        # Limpiar espacios en blanco en columnas de texto
        text_columns = df.select_dtypes(include=['object']).columns
        for col in text_columns:
            try:
                df[col] = df[col].astype(str).str.strip()
                # Reemplazar cadenas vacías con NaN
                df[col] = df[col].replace(['', 'nan', 'None'], None)
            except:
                pass
        
        return df
        
    except Exception as e:
        st.error(f"Error limpiando datos: {e}")
        return df

def analyze_tipo_comedor_fallback(df):
    """Analiza la distribución de tipos de comedores (función de respaldo)"""
    if df is None or df.empty:
        return None, None
    
    # Contar valores en TIPO DE COMEDOR
    if 'TIPO DE COMEDOR' not in df.columns:
        return None, "❌ Columna 'TIPO DE COMEDOR' no encontrada"
    
    tipo_counts = df['TIPO DE COMEDOR'].value_counts()
    
    # Calcular porcentajes
    tipo_percentages = (tipo_counts / len(df)) * 100
    
    # Crear análisis textual
    total_comedores = len(df)
    tipos_disponibles = list(tipo_counts.index)
    
    analysis_text = f"""
    ## 📊 Análisis de Tipos de Comedores
    
    **Resumen General:**
    - **Total de comedores registrados:** {total_comedores:,}
    - **Tipos identificados:** {len(tipos_disponibles)}
    
    **Distribución por tipo:**
    """
    
    for tipo, count in tipo_counts.items():
        percentage = (count / total_comedores) * 100
        analysis_text += f"\n- **{tipo}:** {count:,} comedores ({percentage:.1f}%)"
    
    # Agregar insights adicionales
    if len(tipo_counts) > 0:
        tipo_mas_comun = tipo_counts.index[0]
        analysis_text += f"""
        
        **Insights clave:**
        - El tipo más común es: **{tipo_mas_comun}**
        - Representa el {tipo_percentages.iloc[0]:.1f}% del total de comedores
        """
        
        if len(tipo_counts) > 1:
            segundo_tipo = tipo_counts.index[1]
            analysis_text += f"\n- El segundo tipo más común es: **{segundo_tipo}** ({tipo_percentages.iloc[1]:.1f}%)"
    
    return tipo_counts, analysis_text

def show_connection_status():
    """Muestra el estado de la conexión"""
    if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        st.success("✅ Credenciales configuradas correctamente")
    else:
        st.warning("⚠️ Credenciales no configuradas. Configura los secrets para conectar con Google Sheets.")

def create_filters_sidebar(df):
    """Crea los filtros en el sidebar"""
    st.sidebar.markdown('<div class="filter-header">🔍 Filtros de Búsqueda</div>', unsafe_allow_html=True)
    
    # Crear copia para filtros
    df_filtered = df.copy()
    
    # Filtro por Nombre del Comedor
    if 'NOMBRE DEL COMEDOR' in df.columns:
        comedores_unicos = ['Todos'] + sorted(df['NOMBRE DEL COMEDOR'].dropna().unique().tolist())
        comedor_selected = st.sidebar.selectbox("📍 Nombre del Comedor:", comedores_unicos)
        
        if comedor_selected != 'Todos':
            df_filtered = df_filtered[df_filtered['NOMBRE DEL COMEDOR'] == comedor_selected]
    
    # Filtro por Barrio
    if 'BARRIO' in df.columns:
        barrios_unicos = ['Todos'] + sorted(df_filtered['BARRIO'].dropna().unique().tolist())
        barrio_selected = st.sidebar.selectbox("🏘️ Barrio:", barrios_unicos)
        
        if barrio_selected != 'Todos':
            df_filtered = df_filtered[df_filtered['BARRIO'] == barrio_selected]
    
    # Filtro por Comuna
    if 'COMUNA' in df.columns:
        comunas_unicas = ['Todas'] + sorted([str(x) for x in df_filtered['COMUNA'].dropna().unique() if str(x) != 'nan'])
        comuna_selected = st.sidebar.selectbox("🏛️ Comuna:", comunas_unicas)
        
        if comuna_selected != 'Todas':
            df_filtered = df_filtered[df_filtered['COMUNA'].astype(str) == comuna_selected]
    
    # Filtro por Nodo
    if 'NODO ' in df.columns:
        nodos_unicos = ['Todos'] + sorted([str(x) for x in df_filtered['NODO '].dropna().unique() if str(x) != 'nan'])
        nodo_selected = st.sidebar.selectbox("🔗 Nodo:", nodos_unicos)
        
        if nodo_selected != 'Todos':
            df_filtered = df_filtered[df_filtered['NODO '].astype(str) == nodo_selected]
    
    # Filtro por Nicho
    if 'NICHO ' in df.columns:
        nichos_unicos = ['Todos'] + sorted([str(x) for x in df_filtered['NICHO '].dropna().unique() if str(x) != 'nan'])
        nicho_selected = st.sidebar.selectbox("🎯 Nicho:", nichos_unicos)
        
        if nicho_selected != 'Todos':
            df_filtered = df_filtered[df_filtered['NICHO '].astype(str) == nicho_selected]
    
    # Mostrar información de filtros aplicados
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Registros mostrados:** {len(df_filtered):,} de {len(df):,}")
    
    # Botón para limpiar filtros
    if st.sidebar.button("🔄 Limpiar Filtros"):
        st.rerun()
    
    return df_filtered

def show_metrics(df_filtered, df_original):
    """Muestra las métricas principales"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Total Comedores</h4>
            <h2 style="color: #2E7D32;">{:,}</h2>
        </div>
        """.format(len(df_filtered)), unsafe_allow_html=True)
    
    with col2:
        # Buscar columna de tipos dinámicamente
        tipos_col = None
        for col in df_filtered.columns:
            if 'tipo' in col.lower() and 'comedor' in col.lower():
                tipos_col = col
                break
        
        if tipos_col:
            tipos_activos = len(df_filtered[tipos_col].dropna().unique())
        else:
            tipos_activos = 0
            
        st.markdown("""
        <div class="metric-card">
            <h4>Tipos de Comedores</h4>
            <h2 style="color: #1976D2;">{}</h2>
        </div>
        """.format(tipos_activos), unsafe_allow_html=True)
    
    with col3:
        # Buscar columna de barrios dinámicamente
        barrios_col = None
        for col in df_filtered.columns:
            if 'barrio' in col.lower():
                barrios_col = col
                break
        
        if barrios_col:
            barrios_activos = len(df_filtered[barrios_col].dropna().unique())
        else:
            barrios_activos = 0
            
        st.markdown("""
        <div class="metric-card">
            <h4>Barrios Cubiertos</h4>
            <h2 style="color: #F57C00;">{}</h2>
        </div>
        """.format(barrios_activos), unsafe_allow_html=True)
    
    with col4:
        # Buscar columna de comunas dinámicamente
        comunas_col = None
        for col in df_filtered.columns:
            if 'comuna' in col.lower():
                comunas_col = col
                break
        
        if comunas_col:
            comunas_activas = len(df_filtered[comunas_col].dropna().unique())
        else:
            comunas_activas = 0
            
        st.markdown("""
        <div class="metric-card">
            <h4>Comunas Activas</h4>
            <h2 style="color: #7B1FA2;">{}</h2>
        </div>
        """.format(comunas_activas), unsafe_allow_html=True)

# Función principal
def main():
    # Título principal
    st.markdown('<h1 class="main-header">🍽️ Dashboard Comedores Comunitarios</h1>', unsafe_allow_html=True)
    
    # Mostrar estado de conexión
    show_connection_status()
    
    # Cargar datos
    with st.spinner('Cargando datos desde Google Sheets...'):
        df = load_data_secure()
    
    if df is None:
        st.error("❌ No se pudieron cargar los datos. Verifica la configuración de secrets.")
        st.info("""
        ### 🔧 Configuración necesaria:
        
        1. **En Streamlit Cloud**, configura los secrets con:
           - Credenciales de Google Service Account
           - ID de Google Sheets
           - Nombre de la hoja de trabajo
        
        2. **Para desarrollo local**, crea el archivo `.streamlit/secrets.toml`
        
        3. **Verifica permisos** en Google Sheets y Google Cloud
        """)
        return
    
    # Información básica de los datos
    st.info(f"📊 **Datos cargados exitosamente:** {len(df):,} registros encontrados")
    
    # Crear filtros en sidebar
    df_filtered = create_filters_sidebar(df)
    
    # Mostrar métricas principales
    show_metrics(df_filtered, df)
    
    st.markdown("---")
    
    # Sección de resumen general
    st.markdown("## 📋 Resumen General del Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Información del Dataset
        
        Este dashboard contiene información completa sobre los comedores comunitarios, 
        incluyendo datos de:
        
        - **Ubicación**: Barrios, comunas, nodos y nichos
        - **Gestores**: Información de responsables
        - **Población atendida**: Enfoques diferenciales y etapas vitales
        - **Necesidades y problemáticas** identificadas
        - **Articulaciones** con otras instituciones
        - **Actividades** y líneas de acción
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Páginas Disponibles
        
        Navega por las diferentes secciones utilizando el menú lateral:
        
        - **🥧 Distribución de Tipos de Comedores**: Análisis detallado de los tipos de comedores con gráficos interactivos
        
        *Más páginas de análisis estarán disponibles próximamente...*
        """)
    
    # Información sobre filtros aplicados
    if len(df_filtered) != len(df):
        st.markdown("## 🔍 Filtros Aplicados")
        st.info(f"""
        **Datos filtrados:** Se están mostrando {len(df_filtered):,} de {len(df):,} registros totales.
        
        Los filtros aplicados afectan todas las visualizaciones y análisis en las páginas del dashboard.
        
        Para ver todos los datos, usa el botón "🔄 Limpiar Filtros" en el panel lateral.
        """)
    
    # Sección de vista rápida de datos
    st.markdown("## 👀 Vista Rápida de Datos")
    
    if not df_filtered.empty:
        # Selector de columnas a mostrar
        default_columns = []
        
        # Buscar columnas importantes dinámicamente
        important_patterns = [
            ('TIPO DE COMEDOR', 'tipo.*comedor'),
            ('NOMBRE DEL COMEDOR', 'nombre.*comedor'),
            ('BARRIO', 'barrio'),
            ('COMUNA', 'comuna'),
            ('NODO ', 'nodo'),
            ('NICHO ', 'nicho')
        ]
        
        for expected, pattern in important_patterns:
            found = False
            # Búsqueda exacta
            if expected in df_filtered.columns:
                default_columns.append(expected)
                found = True
            # Búsqueda por patrón si no se encuentra exacta
            elif not found:
                import re
                for col in df_filtered.columns:
                    if re.search(pattern, col.lower()):
                        default_columns.append(col)
                        break
        
        # Limitar a columnas que existen
        available_default_columns = [col for col in default_columns if col in df_filtered.columns]
        
        if available_default_columns:
            selected_columns = st.multiselect(
                "Selecciona las columnas a mostrar:",
                options=df_filtered.columns.tolist(),
                default=available_default_columns[:6],  # Máximo 6 columnas por defecto
                help="Selecciona qué información quieres ver en la tabla"
            )
            
            if selected_columns:
                # Mostrar datos filtrados
                st.dataframe(
                    df_filtered[selected_columns],
                    use_container_width=True,
                    height=400
                )
                
                # Opción para descargar datos
                st.markdown("### 📥 Descargar Datos")
                csv = df_filtered[selected_columns].to_csv(index=False)
                st.download_button(
                    label="📥 Descargar datos filtrados (CSV)",
                    data=csv,
                    file_name=f"comedores_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime='text/csv',
                    help="Descarga los datos actuales con los filtros aplicados"
                )
            else:
                st.info("👆 Selecciona al menos una columna para mostrar los datos.")
        else:
            st.warning("⚠️ No se pudieron identificar las columnas principales automáticamente.")
            
            # Mostrar todas las columnas disponibles como fallback
            st.info("📋 Columnas disponibles en el dataset:")
            cols_per_row = 3
            for i in range(0, len(df_filtered.columns), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(df_filtered.columns[i:i+cols_per_row]):
                    with cols[j]:
                        st.markdown(f"• {col}")
    else:
        st.warning("No hay datos para mostrar con los filtros aplicados.")
    
    # Footer con información adicional
    st.markdown("---")
    
    # Información del sistema
    col_footer1, col_footer2 = st.columns(2)
    
    with col_footer1:
        st.markdown("""
        ### 📖 Cómo usar este dashboard
        
        1. **Filtros**: Usa el panel lateral para filtrar los datos
        2. **Navegación**: Accede a diferentes análisis desde el menú lateral
        3. **Interactividad**: Los gráficos son interactivos - puedes hacer hover, zoom, etc.
        4. **Descargas**: Puedes descargar los datos y análisis en formato CSV
        """)
    
    with col_footer2:
        st.markdown(f"""
        ### ℹ️ Información del Sistema
        
        - **Última actualización**: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        - **Total de registros**: {len(df):,}
        - **Registros mostrados**: {len(df_filtered):,}
        - **Fuente**: Google Sheets
        """)
    
    # Mensaje final
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-top: 20px;'>
        📊 <strong>Dashboard de Comedores Comunitarios</strong><br>
        Desarrollado para el análisis integral de datos de comedores comunitarios<br>
        💡 <em>Usa el menú lateral para navegar entre las diferentes secciones de análisis</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()