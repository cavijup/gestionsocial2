import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Agregar rutas locales
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de la página
st.set_page_config(
    page_title="🥧 Distribución de Tipos de Comedores",
    page_icon="🥧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos locales
try:
    from utils.google_sheets import load_data_from_sheets
    modules_loaded = True
except ImportError:
    modules_loaded = False

# CSS personalizado para esta página
st.markdown("""
<style>
    .page-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #E8F5E8 0%, #C8E6C9 100%);
        border-radius: 10px;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
        margin: 1rem 0;
    }
    .chart-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .analysis-box {
        background-color: #F3E5F5;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #7B1FA2;
        margin: 1rem 0;
    }
    .highlight-stat {
        background-color: #E8F5E8;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

def find_tipo_comedor_column(df):
    """Busca la columna de tipo de comedor en el DataFrame"""
    if df is None:
        return None
    
    # Posibles nombres de la columna
    possible_names = [
        'TIPO DE COMEDOR',
        'Tipo de Comedor',
        'tipo_de_comedor',
        'TIPO COMEDOR'
    ]
    
    # Buscar exacto
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Buscar parcial
    for col in df.columns:
        if 'tipo' in col.lower() and 'comedor' in col.lower():
            return col
    
    return None

def analyze_tipo_comedor(df):
    """Analiza la distribución de tipos de comedores"""
    if df is None or df.empty:
        return None, None, None
    
    # Buscar la columna
    tipo_col = find_tipo_comedor_column(df)
    
    if not tipo_col:
        return None, None, "❌ No se encontró la columna 'TIPO DE COMEDOR'"
    
    # Obtener datos válidos
    valid_data = df[tipo_col].dropna()
    
    if valid_data.empty:
        return None, None, "⚠️ No hay datos válidos en la columna de tipos"
    
    # Contar frecuencias
    tipo_counts = valid_data.value_counts()
    total_comedores = len(valid_data)
    
    # Crear análisis textual
    analysis_text = f"""
## 🥧 Análisis de Tipos de Comedores

**Resumen General:**
- **Total de comedores registrados:** {total_comedores:,}
- **Tipos identificados:** {len(tipo_counts)}
- **Columna utilizada:** {tipo_col}

**Distribución por tipo:**
"""
    
    for tipo, count in tipo_counts.items():
        percentage = (count / total_comedores) * 100
        analysis_text += f"\n- **{tipo}:** {count:,} comedores ({percentage:.1f}%)"
    
    if len(tipo_counts) > 0:
        tipo_mas_comun = tipo_counts.index[0]
        percentage_mas_comun = (tipo_counts.iloc[0] / total_comedores) * 100
        analysis_text += f"""

**Insights Clave:**
- **Tipo más común:** {tipo_mas_comun}
- **Representa el {percentage_mas_comun:.1f}%** del total de comedores
"""
        
        if len(tipo_counts) > 1:
            segundo_tipo = tipo_counts.index[1]
            percentage_segundo = (tipo_counts.iloc[1] / total_comedores) * 100
            analysis_text += f"\n- **Segundo tipo:** {segundo_tipo} ({percentage_segundo:.1f}%)"
    
    return tipo_counts, tipo_col, analysis_text

def create_filters_sidebar(df):
    """Crea los filtros en el sidebar"""
    st.sidebar.markdown("### 🔍 Filtros de Búsqueda")
    
    df_filtered = df.copy()
    
    # Mapeo de columnas esperadas
    column_mapping = {
        'NOMBRE DEL COMEDOR': '📍 Nombre del Comedor',
        'BARRIO': '🏘️ Barrio',
        'COMUNA': '🏛️ Comuna',
        'NODO ': '🔗 Nodo',
        'NICHO ': '🎯 Nicho'
    }
    
    # Buscar columnas que existen
    filter_columns = {}
    for expected_col, label in column_mapping.items():
        found_col = None
        
        if expected_col in df.columns:
            found_col = expected_col
        else:
            for col in df.columns:
                if expected_col.lower().replace(' ', '') in col.lower().replace(' ', ''):
                    found_col = col
                    break
        
        if found_col:
            filter_columns[found_col] = label
    
    # Crear filtros dinámicamente
    applied_filters = {}
    
    for col, label in filter_columns.items():
        if col in df_filtered.columns:
            unique_values = ['Todos'] + sorted([str(x) for x in df_filtered[col].dropna().unique() if str(x) != 'nan'])
            
            if len(unique_values) > 1:
                selected = st.sidebar.selectbox(label, unique_values, key=f"filter_{col}")
                
                if selected != 'Todos':
                    df_filtered = df_filtered[df_filtered[col].astype(str) == selected]
                    applied_filters[col] = selected
    
    # Información de filtros
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Registros mostrados:** {len(df_filtered):,} de {len(df):,}")
    
    if applied_filters:
        st.sidebar.markdown("**Filtros aplicados:**")
        for col, value in applied_filters.items():
            st.sidebar.markdown(f"- {filter_columns.get(col, col)}: {value}")
    
    if st.sidebar.button("🔄 Limpiar Filtros"):
        st.rerun()
    
    return df_filtered

def create_attractive_pie_chart(tipo_counts):
    """Crea un gráfico de pastel más llamativo y profesional"""
    
    # Colores vibrantes y atractivos
    colors = [
        '#FF6B6B',  # Rojo coral
        '#4ECDC4',  # Turquesa
        '#45B7D1',  # Azul cielo
        '#96CEB4',  # Verde menta
        '#FFEAA7',  # Amarillo suave
        '#DDA0DD',  # Ciruela
        '#98D8C8',  # Verde agua
        '#F7DC6F',  # Amarillo dorado
        '#BB8FCE',  # Lavanda
        '#85C1E9'   # Azul claro
    ]
    
    # Extender colores si hay más categorías
    if len(tipo_counts) > len(colors):
        colors = colors * (len(tipo_counts) // len(colors) + 1)
    
    fig = go.Figure(data=[go.Pie(
        labels=tipo_counts.index,
        values=tipo_counts.values,
        hole=0.4,  # Crear un donut chart
        marker=dict(
            colors=colors[:len(tipo_counts)],
            line=dict(color='#FFFFFF', width=3)
        ),
        textinfo='label+percent',
        textposition='auto',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>%{label}</b><br>' +
                      'Cantidad: %{value}<br>' +
                      'Porcentaje: %{percent}<br>' +
                      '<extra></extra>',
        pull=[0.1 if i == 0 else 0 for i in range(len(tipo_counts))]  # Destacar el mayor
    )])
    
    # Añadir texto en el centro del donut
    if len(tipo_counts) > 0:
        total = tipo_counts.sum()
        fig.add_annotation(
            text=f"Total<br><b>{total:,}</b><br>Comedores",
            x=0.5, y=0.5,
            font_size=16,
            font_color="#2E7D32",
            showarrow=False
        )
    
    fig.update_layout(
        title={
            'text': "🥧 Distribución de Tipos de Comedores",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2E7D32', 'family': 'Arial Black'}
        },
        height=600,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=12)
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=120, t=80, b=20)
    )
    
    return fig

def create_summary_table(tipo_counts):
    """Crea tabla resumen de tipos de comedores"""
    total_comedores = tipo_counts.sum()
    
    summary_df = pd.DataFrame({
        'Tipo de Comedor': tipo_counts.index,
        'Cantidad': tipo_counts.values,
        'Porcentaje': [f"{(count/total_comedores)*100:.1f}%" for count in tipo_counts.values],
        'Ranking': range(1, len(tipo_counts) + 1)
    })
    
    return summary_df

def main():
    # Header de la página
    st.markdown('<div class="page-header">🥧 Distribución de Tipos de Comedores</div>', unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner('🔄 Cargando datos desde Google Sheets...'):
        if modules_loaded:
            df = load_data_from_sheets()
        else:
            st.error("❌ Módulos de carga no disponibles")
            return
    
    if df is None:
        st.error("❌ No se pudieron cargar los datos. Verifica la conexión.")
        st.info("💡 **Sugerencia:** Ejecuta `streamlit run debug_app.py` para diagnosticar el problema.")
        return
    
    # Información de datos cargados
    st.markdown(f"""
    <div class="metric-container">
        <h4>📊 Sistema Operativo</h4>
        <p><strong>Registros disponibles:</strong> {len(df):,}</p>
        <p><strong>Última actualización:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros en sidebar
    df_filtered = create_filters_sidebar(df)
    
    # Análisis de tipos de comedores
    tipo_counts, tipo_col, analysis_text = analyze_tipo_comedor(df_filtered)
    
    if tipo_counts is None:
        st.error("❌ No se pudo analizar la columna de tipos de comedores")
        if analysis_text:
            st.info(analysis_text)
        return
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["🥧 Gráfico de Pastel", "📋 Análisis Detallado"])
    
    with tab1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Métricas rápidas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Comedores", f"{tipo_counts.sum():,}")
        
        with col2:
            st.metric("Tipos Diferentes", f"{len(tipo_counts)}")
        
        with col3:
            if len(tipo_counts) > 0:
                porcentaje_principal = (tipo_counts.iloc[0] / tipo_counts.sum()) * 100
                st.metric("Tipo Principal", f"{porcentaje_principal:.1f}%")
        
        with col4:
            if len(tipo_counts) > 1:
                diversidad = len(tipo_counts)
                st.metric("Diversidad", f"{diversidad} tipos")
        
        st.markdown("---")
        
        # Gráfico de pastel llamativo
        if not tipo_counts.empty:
            fig_pie = create_attractive_pie_chart(tipo_counts)
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Tabla resumen
            st.markdown("### 📋 Tabla Resumen")
            summary_df = create_summary_table(tipo_counts)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Descarga
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar resumen (CSV)",
                data=csv,
                file_name=f"tipos_comedores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        else:
            st.warning("⚠️ No hay datos para mostrar con los filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
        
        if analysis_text:
            st.markdown(analysis_text)
            
            if not tipo_counts.empty:
                st.markdown("---")
                
                # Análisis estadístico
                st.markdown("### 🔍 Análisis Estadístico")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    mean_val = tipo_counts.mean()
                    median_val = tipo_counts.median()
                    std_val = tipo_counts.std()
                    
                    st.markdown(f"""
                    <div class="highlight-stat">
                        <strong>Media:</strong> {mean_val:.1f} comedores por tipo
                    </div>
                    <div class="highlight-stat">
                        <strong>Mediana:</strong> {median_val:.1f} comedores
                    </div>
                    <div class="highlight-stat">
                        <strong>Desviación estándar:</strong> {std_val:.1f}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Top 3 tipos
                    st.markdown("**🏆 Top 3 Tipos de Comedores:**")
                    for i, (tipo, count) in enumerate(tipo_counts.head(3).items(), 1):
                        percentage = (count / tipo_counts.sum()) * 100
                        st.markdown(f"{i}. **{tipo}:** {count:,} ({percentage:.1f}%)")
                
                # Análisis de concentración
                st.markdown("### 📊 Análisis de Concentración")
                
                if len(tipo_counts) > 1:
                    concentracion = (tipo_counts.iloc[0] / tipo_counts.sum()) * 100
                    
                    if concentracion > 70:
                        st.error(f"🔴 **Alta concentración:** El tipo principal representa {concentracion:.1f}% del total")
                    elif concentracion > 50:
                        st.warning(f"🟡 **Concentración moderada:** El tipo principal representa {concentracion:.1f}% del total")
                    else:
                        st.success(f"🟢 **Distribución equilibrada:** El tipo principal representa {concentracion:.1f}% del total")
                
                # Recomendaciones
                st.markdown("### 💡 Recomendaciones")
                
                if len(tipo_counts) == 1:
                    st.info("📌 **Tipo único:** Todos los comedores son del mismo tipo. Considerar diversificar la oferta.")
                elif len(tipo_counts) <= 3:
                    st.info("📌 **Baja diversidad:** Pocos tipos de comedores. Evaluar oportunidades de expansión.")
                else:
                    st.success("✅ **Buena diversidad:** Variedad adecuada de tipos de comedores.")
        else:
            st.warning("⚠️ No se pudo generar el análisis con los filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()