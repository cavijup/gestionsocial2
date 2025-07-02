import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime

# Importar módulos locales
try:
    from utils.google_sheets import load_data_from_sheets
    modules_loaded = True
except ImportError:
    modules_loaded = False

# Configuración básica
st.set_page_config(page_title="📊 Análisis de Datos", page_icon="📊", layout="wide")

# CSS compacto
st.markdown("""
<style>
.page-header {font-size: 2.2rem; font-weight: bold; color: #1565C0; text-align: center; 
             margin-bottom: 1.5rem; padding: 1rem; background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%); border-radius: 10px;}
.metric-container, .chart-container, .variable-selector, .chart-info {
    padding: 1rem; border-radius: 8px; margin: 1rem 0; background-color: #f8f9fa;}
.variable-selector {background-color: #E8F5E8; border-left: 4px solid #4CAF50;}
.chart-info {background-color: #F3E5F5; border-left: 4px solid #9C27B0;}
</style>
""", unsafe_allow_html=True)

# Mapeo de columnas
COLUMN_MAPPING = {
    'acciones_aparte': '¿El comedor realiza otras acciones aparte de la preparación y entrega de raciones?',
    'frecuencia_actividades': '¿Con que frecuencia realiza estas actividades y/o procesos?',
    'temas_ejecutados': 'TEMAS O ACTIVIDADES QUE SE HAN EJECUTADO ANTERIORMENTE',
    'articulacion_institucion': 'Para el desarrollo de actividades ¿El comedor se ha articulado con alguna institución?',
    'sector_articulacion': 'De qué sector (Solo se responde, si marcó SI en la anterior pregunta)',
    'lineas_accion': 'VII. LINEAS DE ACCIÓN/TIPOLOGIA DEL COMEDOR',
    'social_comunitaria': 'SOCIAL COMUNITARIA',
    'comercial': 'COMERCIAL',
    'institucional': 'INSTITUCIONAL'
}

def find_column_in_df(df, search_terms):
    """Busca columna en DataFrame"""
    if df is None: return None
    for term in search_terms:
        if term in df.columns: return term
    for col in df.columns:
        for term in search_terms:
            if term.lower() in col.lower(): return col
    return None

def get_available_columns(df):
    """Obtiene columnas disponibles"""
    search_patterns = {
        'acciones_aparte': ['acciones aparte', 'otras acciones', 'preparación y entrega'],
        'frecuencia_actividades': ['frecuencia', 'actividades y/o procesos'],
        'temas_ejecutados': ['TEMAS O ACTIVIDADES', 'ejecutado anteriormente'],
        'articulacion_institucion': ['articulado con alguna institución', 'articulación'],
        'sector_articulacion': ['De qué sector', ''],
        'lineas_accion': ['LINEAS DE ACCIÓN', 'TIPOLOGIA DEL COMEDOR'],
        'social_comunitaria': ['SOCIAL COMUNITARIA', 'Colectivos, JAL'],
        'comercial': ['COMERCIAL', 'Supermercados, tiendas'],
        'institucional': ['INSTITUCIONAL', 'Alcaldía, gobernación']
    }
    
    available = {}
    for key, patterns in search_patterns.items():
        found_col = find_column_in_df(df, patterns)
        if found_col: available[key] = found_col
    return available

def clean_and_process_data(series, max_categories=15):
    """Limpia y procesa datos categóricos para gráfico de barras"""
    if series is None or series.empty: 
        return pd.Series(dtype='object')
    
    # Limpiar datos básicos
    cleaned = series.astype(str).str.strip().replace(['nan', 'None', '', 'NaN'], 'Sin respuesta')
    cleaned = cleaned.replace({'Si': 'Sí', 'si': 'Sí', 'SI': 'Sí', 'No': 'No', 'no': 'No', 'NO': 'No'})
    
    # Si es la columna de temas ejecutados, dividir respuestas múltiples
    if 'TEMAS' in series.name.upper() or 'ACTIVIDADES' in series.name.upper():
        all_responses = []
        for response in cleaned:
            if response and response != 'Sin respuesta':
                # Dividir por comas, punto y coma, o saltos de línea
                split_responses = response.replace(';', ',').replace('\n', ',').split(',')
                for item in split_responses:
                    item = item.strip()
                    if item and len(item) > 2:
                        all_responses.append(item)
            else:
                all_responses.append('Sin respuesta')
        cleaned = pd.Series(all_responses)
    
    # Agrupar categorías menos frecuentes
    value_counts = cleaned.value_counts()
    if len(value_counts) > max_categories:
        top_categories = value_counts.head(max_categories-1)
        others_count = value_counts.iloc[max_categories-1:].sum()
        if others_count > 0:
            # Crear nueva serie con categorías agrupadas
            cleaned = cleaned.apply(lambda x: x if x in top_categories.index else 'Otros')
    
    return cleaned

def create_horizontal_bar_chart(data_series, title, show_percentages=False):
    """Crea un gráfico de barras horizontales"""
    
    # Contar frecuencias
    value_counts = data_series.value_counts()
    
    if value_counts.empty:
        return None
    
    categories = value_counts.index.tolist()
    values = value_counts.values.tolist()
    
    # Calcular porcentajes si se solicita
    if show_percentages:
        total = len(data_series)
        percentages = (value_counts / total * 100).round(1)
        categories = [f"{cat} ({percentages[cat]:.1f}%)" for cat in categories]
    
    # Colores degradados
    colors = px.colors.sequential.Viridis[::-1]
    if len(categories) > len(colors):
        colors = colors * (len(categories) // len(colors) + 1)
    
    # Crear gráfico
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(
            color=colors[:len(categories)],
            line=dict(color='rgba(50, 50, 50, 0.8)', width=1)
        ),
        text=values,
        textposition='outside',
        textfont=dict(size=12, color='black'),
        hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<br><extra></extra>'
    ))
    
    # Layout
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'font': {'size': 20, 'color': '#2C3E50'}},
        xaxis=dict(
            title='Frecuencia', titlefont=dict(size=14), tickfont=dict(size=12),
            gridcolor='rgba(128, 128, 128, 0.3)'
        ),
        yaxis=dict(
            title='Categorías', titlefont=dict(size=14), tickfont=dict(size=11),
            autorange='reversed'
        ),
        height=max(400, len(categories) * 35),
        margin=dict(l=20, r=80, t=80, b=50),
        paper_bgcolor='white', plot_bgcolor='white', showlegend=False
    )
    
    return fig

def main():
    # Header
    st.markdown('<div class="page-header">📊 Análisis de Datos - Gráfico de Barras Laterales</div>', unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner('🔄 Cargando datos...'):
        if not modules_loaded:
            st.error("❌ Módulos de carga no disponibles")
            return
        df = load_data_from_sheets()
    
    if df is None:
        st.error("❌ No se pudieron cargar los datos")
        return
    
    # Info de datos
    st.markdown(f"""<div class="metric-container">
    <h4>📊 Sistema Operativo</h4>
    <p><strong>Registros:</strong> {len(df):,} | <strong>Actualización:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>""", unsafe_allow_html=True)
    
    # Info sobre gráfico de barras
    st.markdown("""<div class="chart-info">
    <h4>📊 Gráfico de Barras Horizontales</h4>
    <p>Visualiza la frecuencia de categorías en una variable seleccionada. Las barras más largas indican mayor frecuencia. 
    Ideal para <strong>análisis univariado</strong> de datos categóricos.</p>
    </div>""", unsafe_allow_html=True)
    
    # Obtener columnas
    available_columns = get_available_columns(df)
    if not available_columns:
        st.error("❌ Columnas no encontradas")
        st.info("📋 Columnas disponibles:")
        st.write(df.columns.tolist())
        return
    
    # Selectores
    st.markdown('<div class="variable-selector">### 🎯 Configuración del Gráfico</div>', unsafe_allow_html=True)
    
    # Selector de variable
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_var_key = st.selectbox(
            "**Selecciona la variable a analizar:**", 
            list(available_columns.keys()),
            format_func=lambda x: COLUMN_MAPPING.get(x, x)
        )
    
    with col2:
        max_categories = st.slider(
            "**Máximo categorías:**",
            min_value=5, max_value=25, value=15, step=1
        )
    
    # Controles adicionales
    col3, col4 = st.columns(2)
    with col3:
        show_percentages = st.checkbox("Mostrar porcentajes", value=False)
    with col4:
        show_table = st.checkbox("Mostrar tabla de datos", value=False)
    
    # Procesar y mostrar
    if selected_var_key in available_columns:
        var_column = available_columns[selected_var_key]
        var_name = COLUMN_MAPPING.get(selected_var_key, selected_var_key)
        
        # Procesar datos
        with st.spinner("🔄 Procesando datos..."):
            processed_data = clean_and_process_data(df[var_column], max_categories)
        
        if processed_data.empty:
            st.warning("⚠️ No hay datos válidos para la variable seleccionada")
            return
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Crear gráfico
        with st.spinner("📊 Generando gráfico..."):
            chart_title = f"Frecuencia de: {var_name}"
            if show_percentages:
                chart_title += " (con porcentajes)"
            
            bar_fig = create_horizontal_bar_chart(processed_data, chart_title, show_percentages)
        
        if bar_fig:
            st.plotly_chart(bar_fig, use_container_width=True)
            
            # Métricas compactas
            col1, col2, col3, col4 = st.columns(4)
            
            value_counts = processed_data.value_counts()
            most_common = value_counts.index[0] if not value_counts.empty else "N/A"
            most_common_count = value_counts.iloc[0] if not value_counts.empty else 0
            
            with col1:
                st.metric("📊 Total Respuestas", f"{len(processed_data):,}")
            with col2:
                st.metric("🎯 Categorías Únicas", f"{processed_data.nunique():,}")
            with col3:
                st.metric("⭐ Más Frecuente", f"{most_common_count}")
            with col4:
                percentage = (most_common_count / len(processed_data)) * 100 if len(processed_data) > 0 else 0
                st.metric("📈 Porcentaje Top", f"{percentage:.1f}%")
            
            # Mostrar el más común
            if most_common != "N/A":
                st.success(f"🏆 **Categoría más frecuente:** {most_common} ({most_common_count} veces)")
            
            # Tabla opcional
            if show_table:
                st.markdown("### 📋 Tabla de Frecuencias")
                value_counts_df = processed_data.value_counts().reset_index()
                value_counts_df.columns = ['Categoría', 'Frecuencia']
                value_counts_df['Porcentaje'] = (value_counts_df['Frecuencia'] / len(processed_data) * 100).round(2)
                st.dataframe(value_counts_df, use_container_width=True)
        else:
            st.error("❌ No se pudo generar el gráfico")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()