import os
from pathlib import Path

# Intentar cargar python-dotenv si está disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

# Configuración de Google Sheets
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1fbs-J474JbvV3USg5aQlLUW9sNqkBjcd63qBU1nJeeI')
WORKSHEET_NAME = os.getenv('WORKSHEET_NAME', 'Respuestas de formulario 1')
CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', 'credentials/repositoriobd-02686e5726f6.json')

# Configuración de la aplicación
APP_TITLE = os.getenv('APP_TITLE', 'Dashboard Comedores Comunitarios')
APP_ICON = os.getenv('APP_ICON', '🍽️')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))  # 5 minutos por defecto

# Configuración de Streamlit
PAGE_CONFIG = {
    'page_title': APP_TITLE,
    'page_icon': APP_ICON,
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Scope de Google Sheets
GOOGLE_SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# Columnas críticas del dataset
CRITICAL_COLUMNS = [
    'TIPO DE COMEDOR',
    'NOMBRE DEL COMEDOR', 
    'BARRIO',
    'COMUNA',
    'NODO ',
    'NICHO '
]

# Columnas para filtros en sidebar
FILTER_COLUMNS = {
    'NOMBRE DEL COMEDOR': {
        'label': '📍 Nombre del Comedor',
        'all_option': 'Todos'
    },
    'BARRIO': {
        'label': '🏘️ Barrio',
        'all_option': 'Todos'
    },
    'COMUNA': {
        'label': '🏛️ Comuna', 
        'all_option': 'Todas'
    },
    'NODO ': {
        'label': '🔗 Nodo',
        'all_option': 'Todos'
    },
    'NICHO ': {
        'label': '🎯 Nicho',
        'all_option': 'Todos'
    }
}

# Configuración de colores para gráficos
COLOR_SCHEMES = {
    'pie_chart': 'Set3',
    'bar_chart': 'viridis',
    'metrics': {
        'primary': '#2E7D32',
        'secondary': '#1976D2', 
        'accent': '#F57C00',
        'highlight': '#7B1FA2'
    }
}

# Configuración de estilos CSS
CUSTOM_CSS = """
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
    .status-warning {
        background-color: #FFF3E0;
        color: #F57C00;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1976D2;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #F57C00;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FFEBEE;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #C62828;
        margin: 1rem 0;
    }
</style>
"""

# Mensajes de la aplicación
MESSAGES = {
    'loading': 'Cargando datos desde Google Sheets...',
    'connection_error': '❌ No se pudieron cargar los datos. Verifica la conexión y credenciales.',
    'no_data': 'No hay datos suficientes para mostrar el gráfico con los filtros aplicados.',
    'data_loaded': '📊 **Datos cargados exitosamente:** {count:,} registros encontrados',
    'records_shown': '**Registros mostrados:** {filtered:,} de {total:,}',
    'clear_filters': '🔄 Limpiar Filtros',
    'download_csv': '📥 Descargar datos filtrados (CSV)',
    'refresh_data': '🔄 Actualizar Datos',
    'last_updated': '🕒 Última actualización: {timestamp}',
    'total_records': '💾 Registros totales: {total:,} | Mostrados: {shown:,}'
}

# Configuración de análisis
ANALYSIS_CONFIG = {
    'max_categories_pie': 15,  # Máximo número de categorías en gráfico de pastel
    'min_records_analysis': 5,  # Mínimo de registros para análisis
    'date_format': '%d/%m/%Y %H:%M',
    'number_format': '{:,}',
    'percentage_format': '{:.1f}%'
}

# Configuración de exportación
EXPORT_CONFIG = {
    'csv_encoding': 'utf-8',
    'excel_engine': 'openpyxl',
    'date_format_export': '%Y%m%d_%H%M%S'
}

# Rutas de archivos
PATHS = {
    'credentials': Path(CREDENTIALS_PATH),
    'assets': Path('assets'),
    'exports': Path('exports'),
    'logs': Path('logs'),
    'temp': Path('temp')
}

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO' if not DEBUG_MODE else 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': PATHS['logs'] / 'app.log' if PATHS['logs'].exists() else None
}

# Validación de configuración
def validate_config():
    """Valida la configuración de la aplicación"""
    issues = []
    
    # Verificar variables críticas
    if not GOOGLE_SHEET_ID:
        issues.append("GOOGLE_SHEET_ID no está configurado")
    
    if not WORKSHEET_NAME:
        issues.append("WORKSHEET_NAME no está configurado")
    
    # Verificar archivo de credenciales
    if not PATHS['credentials'].exists():
        issues.append(f"Archivo de credenciales no encontrado: {PATHS['credentials']}")
    
    return issues

# Configuración de entorno
ENVIRONMENT = {
    'has_dotenv': HAS_DOTENV,
    'debug_mode': DEBUG_MODE,
    'config_issues': validate_config()
}

# Información de la aplicación
APP_INFO = {
    'name': APP_TITLE,
    'version': '1.0.0',
    'description': 'Dashboard para análisis de comedores comunitarios',
    'author': 'Equipo de Desarrollo',
    'repository': 'https://github.com/tu-usuario/comedores-dashboard',
    'documentation': 'https://docs.comedores-dashboard.com'
}

# URLs y enlaces
URLS = {
    'google_sheets_help': 'https://developers.google.com/sheets/api/guides/concepts',
    'streamlit_docs': 'https://docs.streamlit.io/',
    'plotly_docs': 'https://plotly.com/python/',
    'pandas_docs': 'https://pandas.pydata.org/docs/'
}

# Configuración de desarrollo
if DEBUG_MODE:
    # Configuraciones adicionales para desarrollo
    CACHE_TTL = 60  # Cache más corto en desarrollo
    
    # Mostrar información adicional
    SHOW_DEBUG_INFO = True
    SHOW_RAW_DATA = True
    SHOW_CONFIG_INFO = True
else:
    SHOW_DEBUG_INFO = False
    SHOW_RAW_DATA = False
    SHOW_CONFIG_INFO = False

# Función para obtener configuración completa
def get_config():
    """Retorna toda la configuración de la aplicación"""
    return {
        'app': APP_INFO,
        'google_sheets': {
            'sheet_id': GOOGLE_SHEET_ID,
            'worksheet_name': WORKSHEET_NAME,
            'credentials_path': str(PATHS['credentials']),
            'scope': GOOGLE_SCOPE
        },
        'ui': {
            'page_config': PAGE_CONFIG,
            'colors': COLOR_SCHEMES,
            'css': CUSTOM_CSS,
            'messages': MESSAGES
        },
        'data': {
            'critical_columns': CRITICAL_COLUMNS,
            'filter_columns': FILTER_COLUMNS,
            'cache_ttl': CACHE_TTL
        },
        'analysis': ANALYSIS_CONFIG,
        'export': EXPORT_CONFIG,
        'environment': ENVIRONMENT,
        'debug': {
            'debug_mode': DEBUG_MODE,
            'show_debug_info': SHOW_DEBUG_INFO,
            'show_raw_data': SHOW_RAW_DATA,
            'show_config_info': SHOW_CONFIG_INFO
        }
    }