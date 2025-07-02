import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import re
from collections import Counter

# Agregar rutas locales
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de la página
st.set_page_config(
    page_title="📊 Enfoques Diferenciales/Étnicos",
    page_icon="📊",
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
        color: #1976D2;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 10px;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1976D2;
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

def find_enfoques_column(df):
    """Busca la columna de enfoques diferenciales en el DataFrame"""
    if df is None:
        return None
    
    # Posibles nombres de la columna
    possible_names = [
        'ENFOQUES DIFERENCIALES/ETNICOS',
        'ENFOQUES DIFERENCIALES/ÉTNICOS',
        'ENFOQUES DIFERENCIALES/ETNICOS\r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)',
        'ENFOQUES DIFERENCIALES/ÉTNICOS\r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)'
    ]
    
    # Buscar exacto
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Buscar parcial
    for col in df.columns:
        if 'enfoque' in col.lower() and ('diferencial' in col.lower() or 'etnico' in col.lower() or 'étnico' in col.lower()):
            return col
    
    return None

def parse_multiple_options(data_series):
    """Parsea opciones múltiples separadas por comas"""
    all_options = []
    
    for entry in data_series.dropna():
        if pd.isna(entry) or entry == '' or str(entry).lower() in ['nan', 'none']:
            continue
        
        # Dividir por comas y limpiar
        options = [opt.strip() for opt in str(entry).split(',')]
        # Filtrar opciones vacías
        options = [opt for opt in options if opt and opt.lower() not in ['nan', 'none', '']]
        all_options.extend(options)
    
    return all_options

def analyze_enfoques_diferenciales(df):
    """Analiza los enfoques diferenciales/étnicos"""
    if df is None or df.empty:
        return None, None, None
    
    # Buscar la columna
    enfoques_col = find_enfoques_column(df)
    
    if not enfoques_col:
        return None, None, "❌ No se encontró la columna 'ENFOQUES DIFERENCIALES/ETNICOS'"
    
    # Obtener datos válidos
    valid_data = df[enfoques_col].dropna()
    
    if valid_data.empty:
        return None, None, "⚠️ No hay datos válidos en la columna de enfoques diferenciales"
    
    # Parsear opciones múltiples
    all_enfoques = parse_multiple_options(valid_data)
    
    if not all_enfoques:
        return None, None, "⚠️ No se pudieron extraer enfoques válidos de los datos"
    
    # Contar frecuencias
    enfoques_counts = pd.Series(all_enfoques).value_counts()
    
    # Calcular estadísticas
    total_menciones = len(all_enfoques)
    comedores_con_enfoques = len(valid_data)
    total_comedores = len(df)
    
    # Crear análisis textual
    analysis_text = f"""
## 📊 Análisis de Enfoques Diferenciales/Étnicos

**Resumen General:**
- **Total de comedores:** {total_comedores:,}
- **Comedores con enfoques definidos:** {comedores_con_enfoques:,} ({(comedores_con_enfoques/total_comedores)*100:.1f}%)
- **Total de menciones:** {total_menciones:,}
- **Enfoques únicos identificados:** {len(enfoques_counts)}
- **Promedio de enfoques por comedor:** {total_menciones/comedores_con_enfoques:.1f}

**Distribución de Enfoques:**
"""
    
    for enfoque, count in enfoques_counts.head(10).items():
        percentage = (count / total_menciones) * 100
        coverage = (count / total_comedores) * 100
        analysis_text += f"\n- **{enfoque}:** {count:,} menciones ({percentage:.1f}% del total, {coverage:.1f}% de comedores)"
    
    # Insights adicionales
    if len(enfoques_counts) > 0:
        enfoque_principal = enfoques_counts.index[0]
        menciones_principal = enfoques_counts.iloc[0]
        
        analysis_text += f"""

**Insights Clave:**
- **Enfoque más frecuente:** {enfoque_principal}
- **Menciones del enfoque principal:** {menciones_principal:,} ({(menciones_principal/total_menciones)*100:.1f}%)
"""
        
        if len(enfoques_counts) > 1:
            segundo_enfoque = enfoques_counts.index[1]
            menciones_segundo = enfoques_counts.iloc[1]
            analysis_text += f"\n- **Segundo enfoque:** {segundo_enfoque} ({menciones_segundo:,} menciones)"
        
        # Análisis de diversidad
        top_3_percentage = (enfoques_counts.head(3).sum() / total_menciones) * 100
        analysis_text += f"\n- **Concentración:** Los 3 enfoques principales representan el {top_3_percentage:.1f}% de todas las menciones"
        
        # Análisis de cobertura
        enfoques_por_comedor = total_menciones / comedores_con_enfoques
        if enfoques_por_comedor > 2:
            analysis_text += f"\n- **Diversidad:** En promedio, cada comedor atiende {enfoques_por_comedor:.1f} enfoques diferentes"
        elif enfoques_por_comedor > 1.5:
            analysis_text += f"\n- **Enfoque múltiple:** La mayoría de comedores atiende múltiples enfoques poblacionales"
        else:
            analysis_text += f"\n- **Enfoque específico:** La mayoría de comedores se concentra en enfoques específicos"
    
    return enfoques_counts, enfoques_col, analysis_text

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

def create_horizontal_bar_chart(enfoques_counts, title="Distribución de Enfoques Diferenciales/Étnicos"):
    """Crea gráfico de barras horizontales - Top 7 + Otros"""
    
    # Tomar solo los top 7 enfoques
    top_7 = enfoques_counts.head(7)
    
    # Calcular "Otros" si hay más de 7 enfoques
    if len(enfoques_counts) > 7:
        otros_count = enfoques_counts.iloc[7:].sum()
        # Crear nueva serie con Top 7 + Otros
        chart_data = pd.concat([top_7, pd.Series([otros_count], index=['Otros'])])
    else:
        chart_data = top_7
    
    # Crear el gráfico
    fig = go.Figure()
    
    # Colores: degradado azul para los top 7 y gris para "Otros"
    colors = []
    base_colors = px.colors.sequential.Blues_r[:7]  # Solo 7 colores del degradado
    
    for i, (name, count) in enumerate(chart_data.items()):
        if name == 'Otros':
            colors.append('#757575')  # Gris para "Otros"
        else:
            colors.append(base_colors[i % len(base_colors)])
    
    fig.add_trace(go.Bar(
        y=chart_data.index,
        x=chart_data.values,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.1)', width=1)
        ),
        text=chart_data.values,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Menciones: %{x}<br>Porcentaje: %{customdata:.1f}%<extra></extra>',
        customdata=[(count/enfoques_counts.sum())*100 for count in chart_data.values]
    ))
    
    fig.update_layout(
        title={
            'text': "📊 Top 7 Enfoques Diferenciales + Otros",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#1976D2'}
        },
        xaxis_title="Número de Menciones",
        yaxis_title="Enfoques Poblacionales",
        height=420,  # Altura fija para máximo 8 elementos (Top 7 + Otros)
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(l=20, r=80, t=60, b=40)
    )
    
    # Personalizar ejes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        autorange="reversed"  # Para que el más alto esté arriba (orden descendente)
    )
    
    return fig
    
       
    # Tomar los top 15 para mejor visualización
    top_enfoques = enfoques_counts.head(15)
    
    fig = go.Figure()
    
    # Colores degradados
    colors = px.colors.sequential.Blues_r[:len(top_enfoques)]
    
    fig.add_trace(go.Bar(
        y=top_enfoques.index,
        x=top_enfoques.values,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.1)', width=1)
        ),
        text=top_enfoques.values,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Menciones: %{x}<br>Porcentaje: %{customdata:.1f}%<extra></extra>',
        customdata=[(count/enfoques_counts.sum())*100 for count in top_enfoques.values]
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#1976D2'}
        },
        xaxis_title="Número de Menciones",
        yaxis_title="Enfoques Poblacionales",
        height=max(400, len(top_enfoques) * 30),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12),
        margin=dict(l=20, r=80, t=60, b=40)
    )
    
    # Personalizar ejes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )
    
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        autorange="reversed"  # Para que el más alto esté arriba
    )
    
    return fig

def create_summary_table(enfoques_counts):
    """Crea tabla resumen de enfoques"""
    total_menciones = enfoques_counts.sum()
    
    summary_df = pd.DataFrame({
        'Enfoque Poblacional': enfoques_counts.index,
        'Menciones': enfoques_counts.values,
        'Porcentaje': [f"{(count/total_menciones)*100:.1f}%" for count in enfoques_counts.values],
        'Ranking': range(1, len(enfoques_counts) + 1)
    })
    
    return summary_df

def main():
    # Header de la página
    st.markdown('<div class="page-header">📊 Enfoques Diferenciales/Étnicos</div>', unsafe_allow_html=True)
    
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
    
    # Análisis de enfoques diferenciales
    enfoques_counts, enfoques_col, analysis_text = analyze_enfoques_diferenciales(df_filtered)
    
    if enfoques_counts is None:
        st.error("❌ No se pudo analizar la columna de enfoques diferenciales")
        if analysis_text:
            st.info(analysis_text)
        return
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["📊 Gráfico de Barras", "📋 Análisis Detallado"])
    
    with tab1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Métricas rápidas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Menciones", f"{enfoques_counts.sum():,}")
        
        with col2:
            st.metric("Enfoques Únicos", f"{len(enfoques_counts)}")
        
        with col3:
            if len(enfoques_counts) > 0:
                principal_percentage = (enfoques_counts.iloc[0] / enfoques_counts.sum()) * 100
                st.metric("Enfoque Principal", f"{principal_percentage:.1f}%")
        
        with col4:
            # Calcular diversidad (número de enfoques que representan el 80% de menciones)
            cumsum_pct = (enfoques_counts.cumsum() / enfoques_counts.sum() * 100)
            diversidad = len(cumsum_pct[cumsum_pct <= 80]) + 1
            st.metric("Diversidad (Top 80%)", f"{diversidad} enfoques")
        
        st.markdown("---")
        
        # Gráfico de barras horizontales
        if not enfoques_counts.empty:
            fig_bars = create_horizontal_bar_chart(enfoques_counts)
            st.plotly_chart(fig_bars, use_container_width=True)
            
            # Tabla resumen
            st.markdown("### 📋 Tabla Resumen")
            summary_df = create_summary_table(enfoques_counts)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Descarga
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar resumen (CSV)",
                data=csv,
                file_name=f"enfoques_diferenciales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        else:
            st.warning("⚠️ No hay datos para mostrar con los filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
        
        if analysis_text:
            st.markdown(analysis_text)
            
            if not enfoques_counts.empty:
                st.markdown("---")
                
                # Análisis estadístico adicional
                st.markdown("### 🔍 Análisis Estadístico Avanzado")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📈 Estadísticas de Distribución:**")
                    
                    mean_val = enfoques_counts.mean()
                    median_val = enfoques_counts.median()
                    std_val = enfoques_counts.std()
                    
                    st.markdown(f"""
                    <div class="highlight-stat">
                        <strong>Media:</strong> {mean_val:.1f} menciones por enfoque
                    </div>
                    <div class="highlight-stat">
                        <strong>Mediana:</strong> {median_val:.1f} menciones
                    </div>
                    <div class="highlight-stat">
                        <strong>Desviación estándar:</strong> {std_val:.1f}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**🎯 Análisis de Concentración:**")
                    
                    # Calcular índice de concentración (HHI simplificado)
                    total = enfoques_counts.sum()
                    proportions = enfoques_counts / total
                    concentration_index = (proportions ** 2).sum()
                    
                    # Análisis del top 5
                    top5_percentage = (enfoques_counts.head(5).sum() / total) * 100
                    
                    if concentration_index > 0.25:
                        concentration_level = "🔴 Alta concentración"
                    elif concentration_index > 0.15:
                        concentration_level = "🟡 Concentración moderada"
                    else:
                        concentration_level = "🟢 Distribución equilibrada"
                    
                    st.markdown(f"""
                    <div class="highlight-stat">
                        <strong>Nivel de concentración:</strong> {concentration_level}
                    </div>
                    <div class="highlight-stat">
                        <strong>Top 5 enfoques:</strong> {top5_percentage:.1f}% del total
                    </div>
                    <div class="highlight-stat">
                        <strong>Índice de concentración:</strong> {concentration_index:.3f}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Análisis de patrones
                st.markdown("### 🔍 Patrones Identificados")
                
                # Buscar patrones comunes en los nombres
                all_words = []
                for enfoque in enfoques_counts.index:
                    words = re.findall(r'\b\w+\b', enfoque.lower())
                    all_words.extend(words)
                
                word_counts = Counter(all_words)
                common_words = [word for word, count in word_counts.most_common(10) 
                              if word not in ['de', 'en', 'la', 'el', 'y', 'a', 'con', 'del', 'las', 'los', 'para']]
                
                if common_words:
                    st.markdown("**Palabras más frecuentes en los enfoques:**")
                    st.markdown(", ".join(common_words[:8]))
                
                # Recomendaciones
                st.markdown("### 💡 Recomendaciones")
                
                if len(enfoques_counts) > 15:
                    st.info("📌 **Alta diversidad:** Se identifican muchos enfoques diferentes. Considerar agrupar enfoques similares para análisis más claros.")
                
                if enfoques_counts.iloc[0] / enfoques_counts.sum() > 0.5:
                    st.warning("⚠️ **Alta concentración:** Un solo enfoque domina más del 50% de las menciones. Considerar estrategias para diversificar la atención.")
                
                if len(df_filtered) != len(df):
                    cobertura_filtrada = len(df_filtered[find_enfoques_column(df_filtered)].dropna()) / len(df_filtered) * 100
                    st.info(f"📊 **Cobertura con filtros:** {cobertura_filtrada:.1f}% de los comedores filtrados tienen enfoques definidos.")
        else:
            st.warning("⚠️ No se pudo generar el análisis con los filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()