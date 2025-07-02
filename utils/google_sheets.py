import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from pathlib import Path

# Configuración por defecto
DEFAULT_SHEET_ID = "1fbs-J474JbvV3USg5aQlLUW9sNqkBjcd63qBU1nJeeI"
DEFAULT_WORKSHEET_NAME = "Respuestas de formulario 1"
DEFAULT_CREDENTIALS_PATH = "credentials/repositoriobd-02686e5726f6.json"
DEFAULT_CACHE_TTL = 300

# Scope de Google Sheets
GOOGLE_SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def make_headers_unique(headers):
    """
    Hace únicos los headers duplicados agregando sufijos numéricos
    
    Args:
        headers (list): Lista de headers que pueden contener duplicados
    
    Returns:
        list: Lista de headers únicos
    """
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

def get_credentials_path():
    """Busca el archivo de credenciales en diferentes ubicaciones"""
    possible_paths = [
        DEFAULT_CREDENTIALS_PATH,
        "repositoriobd-02686e5726f6.json",
        "../credentials/repositoriobd-02686e5726f6.json",
        "./credentials/repositoriobd-02686e5726f6.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def load_credentials():
    """Carga las credenciales de Google Sheets desde archivo"""
    try:
        credentials_path = get_credentials_path()
        
        if not credentials_path:
            return None
        
        # Cargar credenciales desde archivo JSON
        credentials = Credentials.from_service_account_file(
            credentials_path, 
            scopes=GOOGLE_SCOPE
        )
        
        return credentials
        
    except FileNotFoundError:
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=DEFAULT_CACHE_TTL)
def load_data_from_sheets(sheet_id=None, worksheet_name=None):
    """
    Carga los datos desde Google Sheets
    
    Args:
        sheet_id (str): ID de la hoja de Google Sheets
        worksheet_name (str): Nombre de la hoja de trabajo
    
    Returns:
        pandas.DataFrame: DataFrame con los datos o None si hay error
    """
    try:
        # Usar valores por defecto si no se proporcionan
        sheet_id = sheet_id or DEFAULT_SHEET_ID
        worksheet_name = worksheet_name or DEFAULT_WORKSHEET_NAME
        
        # Cargar credenciales
        credentials = load_credentials()
        if credentials is None:
            return None
        
        # Autorizar el cliente
        gc = gspread.authorize(credentials)
        
        # Abrir la hoja de cálculo
        try:
            spreadsheet = gc.open_by_key(sheet_id)
        except gspread.SpreadsheetNotFound:
            return None
        except gspread.exceptions.APIError as e:
            return None
        
        # Seleccionar la hoja de trabajo
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return None
        
        # Obtener todos los datos manejando headers duplicados
        try:
            # Intentar primero el método estándar
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
        except Exception as e:
            if "header row in the worksheet is not unique" in str(e):
                # Método alternativo: obtener datos como lista de listas
                all_values = worksheet.get_all_values()
                
                if not all_values:
                    return None
                
                # Tomar la primera fila como headers y hacer únicos
                headers = all_values[0]
                unique_headers = make_headers_unique(headers)
                
                # Crear DataFrame con headers únicos
                data_rows = all_values[1:]  # Excluir header
                df = pd.DataFrame(data_rows, columns=unique_headers)
            else:
                raise e
        
        if df.empty:
            return None
        
        # Limpiar datos básicos
        df = clean_dataframe(df)
        
        return df
        
    except Exception as e:
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
        return df

def validate_connection(sheet_id=None, worksheet_name=None):
    """
    Valida la conexión con Google Sheets
    
    Args:
        sheet_id (str): ID de la hoja de Google Sheets
        worksheet_name (str): Nombre de la hoja de trabajo
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        # Usar valores por defecto si no se proporcionan
        sheet_id = sheet_id or DEFAULT_SHEET_ID
        worksheet_name = worksheet_name or DEFAULT_WORKSHEET_NAME
        
        # Cargar credenciales
        credentials = load_credentials()
        if credentials is None:
            return False
        
        # Autorizar el cliente
        gc = gspread.authorize(credentials)
        
        # Intentar abrir la hoja
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Intentar obtener una celda para verificar acceso
        worksheet.acell('A1')
        
        return True
        
    except Exception:
        return False

def get_sheet_info(sheet_id=None):
    """
    Obtiene información sobre la hoja de cálculo
    
    Args:
        sheet_id (str): ID de la hoja de Google Sheets
    
    Returns:
        dict: Información de la hoja o None si hay error
    """
    try:
        sheet_id = sheet_id or DEFAULT_SHEET_ID
        
        credentials = load_credentials()
        if credentials is None:
            return None
        
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_key(sheet_id)
        
        # Obtener información básica
        info = {
            'title': spreadsheet.title,
            'url': spreadsheet.url,
            'worksheets': [ws.title for ws in spreadsheet.worksheets()],
            'sheet_count': len(spreadsheet.worksheets())
        }
        
        return info
        
    except Exception as e:
        return None

def refresh_data():
    """Fuerza la recarga de datos limpiando el cache"""
    load_data_from_sheets.clear()

# Función de diagnóstico completa (solo para debug_app.py)
def diagnose_connection():
    """Ejecuta un diagnóstico completo de la conexión"""
    st.markdown("### 🔍 Diagnóstico de Conexión")
    
    # 1. Verificar archivo de credenciales
    st.markdown("#### 1. Verificación de credenciales")
    credentials_path = get_credentials_path()
    if credentials_path:
        st.success(f"✅ Archivo de credenciales encontrado: `{credentials_path}`")
    else:
        st.error("❌ Archivo de credenciales no encontrado")
        return
    
    # 2. Cargar credenciales
    st.markdown("#### 2. Carga de credenciales")
    credentials = load_credentials()
    if credentials:
        st.success("✅ Credenciales cargadas correctamente")
    else:
        st.error("❌ Error al cargar credenciales")
        return
    
    # 3. Probar conexión
    st.markdown("#### 3. Prueba de conexión")
    if validate_connection():
        st.success("✅ Conexión exitosa con Google Sheets")
    else:
        st.error("❌ Error de conexión con Google Sheets")
        return
    
    # 4. Información de la hoja
    st.markdown("#### 4. Información de la hoja")
    info = get_sheet_info()
    if info:
        st.success("✅ Información de la hoja obtenida")
        st.json(info)
    else:
        st.error("❌ Error al obtener información de la hoja")
        return
    
    # 5. Prueba de carga de datos
    st.markdown("#### 5. Prueba de carga de datos")
    try:
        df = load_data_from_sheets()
        if df is not None:
            st.success(f"✅ Datos cargados exitosamente: {len(df)} registros")
            
            # Mostrar información detallada de las columnas
            st.markdown("##### Información de columnas:")
            col_info = pd.DataFrame({
                'Columna': df.columns,
                'Tipo': df.dtypes.astype(str),
                'No Nulos': df.count(),
                'Únicos': [df[col].nunique() for col in df.columns]
            })
            st.dataframe(col_info, use_container_width=True)
            
            # Mostrar muestra de datos
            st.markdown("##### Muestra de datos (primeras 3 filas):")
            st.dataframe(df.head(3), use_container_width=True)
        else:
            st.error("❌ Error al cargar datos")
            return
    except Exception as e:
        st.error(f"❌ Error en carga de datos: {str(e)}")
        return
    
    st.success("🎉 ¡Diagnóstico completado exitosamente!")

def show_column_mapping():
    """Muestra un mapeo de columnas para identificar problemas"""
    st.markdown("### 🗂️ Mapeo de Columnas")
    
    try:
        df = load_data_from_sheets()
        if df is not None:
            st.markdown("#### Columnas encontradas en la hoja:")
            
            # Crear tabla con información de columnas
            column_data = []
            for i, col in enumerate(df.columns):
                sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else "N/A"
                column_data.append({
                    'Índice': i,
                    'Nombre de Columna': col,
                    'Tipo': str(df[col].dtype),
                    'Valores No Nulos': df[col].count(),
                    'Ejemplo': str(sample_value)[:50] + "..." if len(str(sample_value)) > 50 else str(sample_value)
                })
            
            columns_df = pd.DataFrame(column_data)
            st.dataframe(columns_df, use_container_width=True)
            
            # Buscar columnas críticas
            st.markdown("#### Búsqueda de columnas críticas:")
            critical_search = [
                'TIPO DE COMEDOR',
                'NOMBRE DEL COMEDOR',
                'BARRIO', 
                'COMUNA',
                'NODO',
                'NICHO'
            ]
            
            for search_term in critical_search:
                matches = [col for col in df.columns if search_term.lower() in col.lower()]
                if matches:
                    st.success(f"✅ '{search_term}' encontrado en: {matches}")
                else:
                    st.warning(f"⚠️ '{search_term}' no encontrado")
        
    except Exception as e:
        st.error(f"Error al mostrar mapeo: {str(e)}")