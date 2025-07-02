import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
from collections import Counter

# Agregar rutas locales
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuración de la página
st.set_page_config(
    page_title="🔄 Etapa Vital",
    page_icon="🔄",
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
        color: #F57C00;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #FFF3E0 0%, #FFCC02 100%);
        border-radius: 10px;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #F57C00;
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
        background-color: #FFF8E1;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FF8F00;
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

def find_etapa_vital_column(df):
    """Busca la columna de etapa vital en el DataFrame"""
    if df is None:
        return None
    
    # Posibles nombres de la columna
    possible_names = [
        'ETAPA VITAL',
        'ETAPA VITAL \r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)',
        'ETAPAS VITALES',
        'EDAD',
        'EDADES'
    ]
    
    # Buscar exacto
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Buscar parcial
    for col in df.columns:
        if 'etapa' in col.lower() and 'vital' in col.lower():
            return col
        elif 'edad' in col.lower() or 'edades' in col.lower():
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

def analyze_etapa_vital(df):
    """Analiza las etapas vitales"""
    if df is None or df.empty:
        return None, None, None
    
    # Buscar la columna
    etapa_col = find_etapa_vital_column(df)
    
    if not etapa_col:
        return None, None, "❌ No se encontró la columna 'ETAPA VITAL'"
    
    # Obtener datos válidos
    valid_data = df[etapa_col].dropna()
    
    if valid_data.empty:
        return None, None, "⚠️ No hay datos válidos en la columna de etapa vital"
    
    # Parsear opciones múltiples
    all_etapas = parse_multiple_options(valid_data)
    
    if not all_etapas:
        return None, None, "⚠️ No se pudieron extraer etapas vitales válidas de los datos"
    
    # Contar frecuencias
    etapa_counts = pd.Series(all_etapas).value_counts()
    
    # Calcular estadísticas
    total_menciones = len(all_etapas)
    comedores_con_etapas = len(valid_data)
    total_comedores = len(df)
    
    # Crear análisis textual
    analysis_text = f"""
## 🔄 Análisis de Etapas Vitales

**Resumen General:**
- **Total de comedores:** {total_comedores:,}
- **Comedores con etapas definidas:** {comedores_con_etapas:,} ({(comedores_con_etapas/total_comedores)*100:.1f}%)
- **Total de menciones:** {total_menciones:,}
- **Etapas únicas identificadas:** {len(etapa_counts)}
- **Promedio de etapas por comedor:** {total_menciones/comedores_con_etapas:.1f}

**Distribución por Etapas Vitales:**
"""
    
    for etapa, count in etapa_counts.head(10).items():
        percentage = (count / total_menciones) * 100
        coverage = (count / total_comedores) * 100
        analysis_text += f"\n- **{etapa}:** {count:,} menciones ({percentage:.1f}% del total, {coverage:.1f}% de comedores)"
    
    # Insights adicionales
    if len(etapa_counts) > 0:
        etapa_principal = etapa_counts.index[0]
        menciones_principal = etapa_counts.iloc[0]
        
        analysis_text += f"""

**Insights Clave:**
- **Etapa más atendida:** {etapa_principal}
- **Menciones de la etapa principal:** {menciones_principal:,} ({(menciones_principal/total_menciones)*100:.1f}%)
"""
        
        if len(etapa_counts) > 1:
            segunda_etapa = etapa_counts.index[1]
            menciones_segunda = etapa_counts.iloc[1]
            analysis_text += f"\n- **Segunda etapa:** {segunda_etapa} ({menciones_segunda:,} menciones)"
        
        # Análisis de diversidad etaria
        etapas_por_comedor = total_menciones / comedores_con_etapas
        if etapas_por_comedor > 3:
            analysis_text += f"\n- **Atención integral:** Los comedores atienden múltiples etapas vitales (promedio: {etapas_por_comedor:.1f})"
        elif etapas_por_comedor > 2:
            analysis_text += f"\n- **Atención diversa:** Mayoría de comedores atiende varias etapas vitales"
        else:
            analysis_text += f"\n- **Atención especializada:** Comedores se concentran en etapas específicas"
    
    return etapa_counts, etapa_col, analysis_text

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

def create_horizontal_bar_chart(etapa_counts, title="Distribución por Etapas Vitales"):
    """Crea gráfico de barras horizontales"""
    
    # Tomar los top 15 para mejor visualización
    top_etapas = etapa_counts.head(15)
    
    fig = go.Figure()
    
    # Colores degradados en tonos naranjas/amarillos
    colors = px.colors.sequential.YlOrRd_r[:len(top_etapas)]
    
    fig.add_trace(go.Bar(
        y=top_etapas.index,
        x=top_etapas.values,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.1)', width=1)
        ),
        text=top_etapas.values,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Menciones: %{x}<br>Porcentaje: %{customdata:.1f}%<extra></extra>',
        customdata=[(count/etapa_counts.sum())*100 for count in top_etapas.values]
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#F57C00'}
        },
        xaxis_title="Número de Menciones",
        yaxis_title="Etapas Vitales",
        height=max(400, len(top_etapas) * 30),
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

def create_summary_table(etapa_counts):
    """Crea tabla resumen de etapas vitales"""
    total_menciones = etapa_counts.sum()
    
    summary_df = pd.DataFrame({
        'Etapa Vital': etapa_counts.index,
        'Menciones': etapa_counts.values,
        'Porcentaje': [f"{(count/total_menciones)*100:.1f}%" for count in etapa_counts.values],
        'Ranking': range(1, len(etapa_counts) + 1)
    })
    
    return summary_df

def main():
    # Header de la página
    st.markdown('<div class="page-header">🔄 Etapa Vital</div>', unsafe_allow_html=True)
    
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
    
    # Análisis de etapas vitales
    etapa_counts, etapa_col, analysis_text = analyze_etapa_vital(df_filtered)
    
    if etapa_counts is None:
        st.error("❌ No se pudo analizar la columna de etapa vital")
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
            st.metric("Total Menciones", f"{etapa_counts.sum():,}")
        
        with col2:
            st.metric("Etapas Únicas", f"{len(etapa_counts)}")
        
        with col3:
            if len(etapa_counts) > 0:
                principal_percentage = (etapa_counts.iloc[0] / etapa_counts.sum()) * 100
                st.metric("Etapa Principal", f"{principal_percentage:.1f}%")
        
        with col4:
            # Promedio de etapas por comedor
            df_con_etapas = df_filtered[find_etapa_vital_column(df_filtered)].dropna()
            if len(df_con_etapas) > 0:
                promedio_etapas = etapa_counts.sum() / len(df_con_etapas)
                st.metric("Promedio/Comedor", f"{promedio_etapas:.1f}")
        
        st.markdown("---")
        
        # Gráfico principal de etapas
        if not etapa_counts.empty:
            fig_bars = create_horizontal_bar_chart(etapa_counts)
            st.plotly_chart(fig_bars, use_container_width=True)
            
            # Tabla resumen
            st.markdown("### 📋 Tabla Resumen")
            summary_df = create_summary_table(etapa_counts)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Descarga
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Descargar resumen (CSV)",
                data=csv,
                file_name=f"etapas_vitales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        else:
            st.warning("⚠️ No hay datos para mostrar con los filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
        
        if analysis_text:
            st.markdown(analysis_text)
            
            if not etapa_counts.empty:
                st.markdown("---")
                
                # Análisis estadístico simplificado
                st.markdown("### 🔍 Análisis Estadístico")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    mean_val = etapa_counts.mean()
                    median_val = etapa_counts.median()
                    std_val = etapa_counts.std()
                    
                    st.markdown(f"""
                    <div class="highlight-stat">
                        <strong>Media:</strong> {mean_val:.1f} menciones por etapa
                    </div>
                    <div class="highlight-stat">
                        <strong>Mediana:</strong> {median_val:.1f} menciones
                    </div>
                    <div class="highlight-stat">
                        <strong>Desviación estándar:</strong> {std_val:.1f}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Top 3 etapas
                    st.markdown("**🏆 Top 3 Etapas Vitales:**")
                    for i, (etapa, count) in enumerate(etapa_counts.head(3).items(), 1):
                        percentage = (count / etapa_counts.sum()) * 100
                        st.markdown(f"{i}. **{etapa}:** {count:,} ({percentage:.1f}%)")
                
                # Recomendaciones específicas
                st.markdown("### 💡 Recomendaciones")
                
                if len(etapa_counts) > 10:
                    st.info("📌 **Alta diversidad etaria:** Considerar programas específicos por grupo de edad para optimizar la atención.")
                
                principal_etapa_pct = etapa_counts.iloc[0] / etapa_counts.sum()
                if principal_etapa_pct > 0.4:
                    st.warning("⚠️ **Concentración etaria:** Una etapa domina significativamente. Evaluar necesidades de otros grupos.")
                
                if len(etapa_counts) < 5:
                    st.info("📊 **Oportunidad de expansión:** Considerar ampliar cobertura a más grupos etarios.")
        else:
            st.warning("⚠️ No se pudo generar el análisis con los filtros aplicados.")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()