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

def make_headers_unique(headers):
    """Hace únicos los headers duplicados agregando sufijos numéricos"""
    unique_headers = []
    header_counts = {}
    
    for header in headers:
        if header in header_counts:
            header_counts[header] += 1
            unique_header = f"{header}_{header_counts[header]}"
        else:
            header_counts[header] = 0
            unique_header = header
        
        unique_headers.append(unique_header)
    
    return unique_headers

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
        
        # Manejar headers duplicados
        try:
            # Intentar método estándar primero
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
        except Exception as e:
            if "header row" in str(e) and ("unique" in str(e) or "duplicates" in str(e)):
                # Método alternativo para headers duplicados
                st.info("🔧 Detectados headers duplicados, aplicando corrección automática...")
                
                # Obtener datos como lista de listas
                all_values = worksheet.get_all_values()
                
                if not all_values:
                    st.error("❌ La hoja de cálculo está vacía")
                    return None
                
                # Tomar la primera fila como headers y hacer únicos
                headers = all_values[0]
                unique_headers = make_headers_unique(headers)
                
                # Crear DataFrame con headers únicos
                data_rows = all_values[1:]  # Excluir header
                df = pd.DataFrame(data_rows, columns=unique_headers)
                
                st.success(f"✅ Headers duplicados corregidos automáticamente")
            else:
                raise e
        
        if df.empty:
            st.warning("⚠️ La hoja de cálculo no contiene datos")
            return None
        
        # Limpiar datos básicos
        df = clean_dataframe(df)
        
        return df
        
    except gspread.SpreadsheetNotFound:
        st.error("❌ Hoja de cálculo no encontrada. Verifica el sheet_id en los secrets.")
        return None
    except gspread.WorksheetNotFound:
        st.error("❌ Hoja de trabajo no encontrada. Verifica el worksheet_name en los secrets.")
        return None
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
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
    
    # Buscar columna de tipo de comedor de forma flexible
    tipo_col = None
    for col in df.columns:
        if 'tipo' in col.lower() and 'comedor' in col.lower():
            tipo_col = col
            break
    
    if not tipo_col:
        return None, "❌ No se encontró columna de 'TIPO DE COMEDOR'"
    
    # Contar valores en la columna encontrada
    tipo_counts = df[tipo_col].dropna().value_counts()
    
    if tipo_counts.empty:
        return None, "⚠️ No hay datos válidos en la columna de tipos"
    
    # Calcular porcentajes
    tipo_percentages = (tipo_counts / len(df.dropna(subset=[tipo_col]))) * 100
    
    # Crear análisis textual
    total_comedores = len(df.dropna(subset=[tipo_col]))
    tipos_disponibles = list(tipo_counts.index)
    
    analysis_text = f"""
    ## 📊 Análisis de Tipos de Comedores
    
    **Resumen General:**
    - **Total de comedores registrados:** {total_comedores:,}
    - **Tipos identificados:** {len(tipos_disponibles)}
    - **Columna utilizada:** {tipo_col}
    
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

def find_column_flexible(df, search_terms):
    """Busca una columna de forma flexible"""
    for term in search_terms:
        # Búsqueda exacta
        if term in df.columns:
            return term
        # Búsqueda parcial
        for col in df.columns:
            if term.lower() in col.lower():
                return col
    return None

def create_filters_sidebar(df):
    """Crea los filtros en el sidebar"""
    st.sidebar.markdown('<div class="filter-header">🔍 Filtros de Búsqueda</div>', unsafe_allow_html=True)
    
    # Crear copia para filtros
    df_filtered = df.copy()
    
    # Definir columnas a buscar
    filter_configs = [
        (['NOMBRE DEL COMEDOR', 'NOMBRE', 'COMEDOR'], '📍 Nombre del Comedor:', 'Todos'),
        (['BARRIO'], '🏘️ Barrio:', 'Todos'),
        (['COMUNA'], '🏛️ Comuna:', 'Todas'),
        (['NODO ', 'NODO'], '🔗 Nodo:', 'Todos'),
        (['NICHO ', 'NICHO'], '🎯 Nicho:', 'Todos')
    ]
    
    applied_filters = 0
    
    for search_terms, label, default_option in filter_configs:
        found_col = find_column_flexible(df, search_terms)
        
        if found_col:
            unique_values = [default_option] + sorted([
                str(x) for x in df_filtered[found_col].dropna().unique() 
                if str(x) not in ['nan', 'None', '']
            ])
            
            if len(unique_values) > 1:
                selected = st.sidebar.selectbox(label, unique_values, key=f"filter_{found_col}")
                
                if selected != default_option:
                    df_filtered = df_filtered[df_filtered[found_col].astype(str) == selected]
                    applied_filters += 1
    
    # Mostrar información de filtros aplicados
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Registros mostrados:** {len(df_filtered):,} de {len(df):,}")
    
    if applied_filters > 0:
        st.sidebar.markdown(f"**Filtros activos:** {applied_filters}")
    
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
        tipo_col = find_column_flexible(df_filtered, ['TIPO DE COMEDOR', 'TIPO', 'COMEDOR'])
        
        if tipo_col:
            tipos_activos = len(df_filtered[tipo_col].dropna().unique())
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
        barrio_col = find_column_flexible(df_filtered, ['BARRIO'])
        
        if barrio_col:
            barrios_activos = len(df_filtered[barrio_col].dropna().unique())
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
        comuna_col = find_column_flexible(df_filtered, ['COMUNA'])
        
        if comuna_col:
            comunas_activas = len(df_filtered[comuna_col].dropna().unique())
        else:
            comunas_activas = 0
            
        st.markdown("""
        <div class="metric-card">
            <h4>Comunas Activas</h4>
            <h2 style="color: #7B1FA2;">{}</h2>
        </div>
        """.format(comunas_activas), unsafe_allow_html=True)

def show_data_info(df):
    """Muestra información sobre los datos cargados"""
    st.markdown("## 📋 Información del Dataset")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **📊 Resumen de Datos:**
        - **Filas:** {len(df):,}
        - **Columnas:** {len(df.columns)}
        - **Memoria:** {df.memory_usage(deep=True).sum() / 1024:.1f} KB
        """)
    
    with col2:
        st.markdown(f"""
        **🕒 Información Temporal:**
        - **Cargado:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        - **Fuente:** Google Sheets
        """)

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
        st.error("❌ No se pudieron cargar los datos.")
        st.info("""
        ### 🔧 Pasos para solucionar:
        
        1. **Verifica los secrets** en Streamlit Cloud
        2. **Confirma el ID de Google Sheets** y nombre de la hoja
        3. **Asegúrate de que la cuenta de servicio** tenga acceso a la hoja
        4. **Revisa los logs** para errores específicos
        """)
        return
    
    # Información básica de los datos
    st.success(f"📊 **Datos cargados exitosamente:** {len(df):,} registros encontrados")
    
    # Mostrar información del dataset
    show_data_info(df)
    
    # Crear filtros en sidebar
    df_filtered = create_filters_sidebar(df)
    
    # Mostrar métricas principales
    show_metrics(df_filtered, df)
    
    st.markdown("---")
    
    # Información sobre filtros aplicados
    if len(df_filtered) != len(df):
        st.markdown("## 🔍 Filtros Aplicados")
        st.info(f"""
        **Datos filtrados:** Se están mostrando {len(df_filtered):,} de {len(df):,} registros totales.
        
        Los filtros aplicados afectan todas las visualizaciones y análisis en las páginas del dashboard.
        """)
    
    # Sección de vista rápida de datos
    st.markdown("## 👀 Vista Rápida de Datos")
    
    if not df_filtered.empty:
        # Mostrar las primeras 5 columnas por defecto
        default_columns = df_filtered.columns[:min(6, len(df_filtered.columns))].tolist()
        
        selected_columns = st.multiselect(
            "Selecciona las columnas a mostrar:",
            options=df_filtered.columns.tolist(),
            default=default_columns,
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
        st.warning("No hay datos para mostrar con los filtros aplicados.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px; background-color: #f8f9fa; border-radius: 10px;'>
        📊 <strong>Dashboard de Comedores Comunitarios</strong><br>
        Desarrollado para el análisis integral de datos de comedores comunitarios<br>
        💡 <em>Usa el menú lateral para navegar entre las diferentes secciones de análisis</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()