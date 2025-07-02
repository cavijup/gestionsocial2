import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except Exception as e:
                    pass  # Silenciar errores en las páginas
        
        # Limpiar espacios en blanco en columnas de texto
        text_columns = df.select_dtypes(include=['object']).columns
        for col in text_columns:
            try:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(['', 'nan', 'None'], None)
            except Exception as e:
                pass  # Silenciar errores en las páginas
        
        return df
        
    except Exception as e:
        return df

@st.cache_data(ttl=300)
def load_data_from_sheets():
    """
    Carga datos usando configuración segura desde Streamlit Secrets
    Compatible con las páginas adicionales
    """
    try:
        # Verificar si existen los secrets
        if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
            return None
        
        # Obtener credenciales desde secrets
        credentials_info = dict(st.secrets["gcp_service_account"])
        
        # Usar scope actualizado
        scope = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
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
        
        # Intentar obtener la hoja específica
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return None
        
        # Manejar headers duplicados
        try:
            # Intentar método estándar primero
            data = worksheet.get_all_records()
            if not data:
                return None
            df = pd.DataFrame(data)
            
        except Exception as e:
            if "header row" in str(e).lower() and ("unique" in str(e).lower() or "duplicates" in str(e).lower()):
                # Método alternativo para headers duplicados
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
        
    except gspread.SpreadsheetNotFound:
        return None
    except Exception as e:
        return None

# Función alternativa para compatibilidad con app.py principal
def load_data_secure():
    """Alias para compatibilidad con app.py principal"""
    return load_data_from_sheets()