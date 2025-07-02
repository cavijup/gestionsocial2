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
    page_title="🎯 Necesidades",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar módulos locales
try:
    from utils.google_sheets import load_data_from_sheets
    modules_loaded = True
except ImportError:
    modules_loaded = False

# CSS personalizado
st.markdown("""
<style>
    .page-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #D32F2F;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #FFEBEE 0%, #FFCDD2 100%);
        border-radius: 10px;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #D32F2F;
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
        background-color: #FFEBEE;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #D32F2F;
        margin: 1rem 0;
    }
    .highlight-stat {
        background-color: #E8F5E8;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #4CAF50;
    }
    .priority-high {
        background-color: #FFEBEE;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #F44336;
    }
    .priority-medium {
        background-color: #FFF3E0;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #FF9800;
    }
</style>
""", unsafe_allow_html=True)

def find_necesidades_column(df):
    """Busca la columna de necesidades"""
    if df is None:
        return None
    
    possible_names = ['NECESIDADES', 'NECESIDAD', 'REQUERIMIENTOS', 'DEMANDAS']
    
    # Buscar exacto
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Buscar parcial
    for col in df.columns:
        if 'necesidad' in col.lower():
            return col
    
    return None

def parse_multiple_options(data_series):
    """Parsea opciones múltiples separadas por comas"""
    all_options = []
    for entry in data_series.dropna():
        if pd.isna(entry) or entry == '' or str(entry).lower() in ['nan', 'none']:
            continue
        options = [opt.strip() for opt in str(entry).split(',')]
        options = [opt for opt in options if opt and opt.lower() not in ['nan', 'none', '']]
        all_options.extend(options)
    return all_options

def categorize_necesidades(necesidades_counts):
    """Categoriza necesidades por nivel de prioridad"""
    total = necesidades_counts.sum()
    high_priority = {}
    medium_priority = {}
    low_priority = {}
    
    for necesidad, count in necesidades_counts.items():
        percentage = (count / total) * 100
        if percentage >= 10:
            high_priority[necesidad] = count
        elif percentage >= 3:
            medium_priority[necesidad] = count
        else:
            low_priority[necesidad] = count
    
    return high_priority, medium_priority, low_priority

def analyze_necesidades(df):
    """Analiza las necesidades identificadas"""
    if df is None or df.empty:
        return None, None, None
    
    necesidades_col = find_necesidades_column(df)
    if not necesidades_col:
        return None, None, "❌ No se encontró la columna 'NECESIDADES'"
    
    valid_data = df[necesidades_col].dropna()
    if valid_data.empty:
        return None, None, "⚠️ No hay datos válidos en la columna de necesidades"
    
    all_necesidades = parse_multiple_options(valid_data)
    if not all_necesidades:
        return None, None, "⚠️ No se pudieron extraer necesidades válidas"
    
    necesidades_counts = pd.Series(all_necesidades).value_counts()
    total_menciones = len(all_necesidades)
    comedores_con_necesidades = len(valid_data)
    total_comedores = len(df)
    
    # Categorizar por prioridad
    high, medium, low = categorize_necesidades(necesidades_counts)
    
    # Análisis textual
    analysis_text = f"""
## 🎯 Análisis de Necesidades Identificadas

**Resumen:**
- **Total comedores:** {total_comedores:,}
- **Con necesidades definidas:** {comedores_con_necesidades:,} ({(comedores_con_necesidades/total_comedores)*100:.1f}%)
- **Total menciones:** {total_menciones:,}
- **Necesidades únicas:** {len(necesidades_counts)}
- **Promedio por comedor:** {total_menciones/comedores_con_necesidades:.1f}

**Clasificación por Prioridad:**
- **🔴 Alta prioridad (≥10%):** {len(high)} necesidades
- **🟡 Media prioridad (3-10%):** {len(medium)} necesidades  
- **⚪ Baja prioridad (<3%):** {len(low)} necesidades

**Top 8 Necesidades Críticas:**
"""
    
    for necesidad, count in necesidades_counts.head(8).items():
        percentage = (count / total_menciones) * 100
        priority = "🔴" if percentage >= 10 else "🟡" if percentage >= 3 else "⚪"
        analysis_text += f"\n- {priority} **{necesidad}:** {count:,} ({percentage:.1f}%)"
    
    return necesidades_counts, necesidades_col, analysis_text

def create_filters_sidebar(df):
    """Crea filtros en sidebar"""
    st.sidebar.markdown("### 🔍 Filtros")
    df_filtered = df.copy()
    
    filters = {
        'BARRIO': '🏘️ Barrio', 
        'COMUNA': '🏛️ Comuna',
        'NODO ': '🔗 Nodo',
        'NICHO ': '🎯 Nicho'
    }
    
    for col, label in filters.items():
        found_col = col if col in df.columns else next((c for c in df.columns if col.lower().replace(' ', '') in c.lower().replace(' ', '')), None)
        
        if found_col and found_col in df_filtered.columns:
            values = ['Todos'] + sorted([str(x) for x in df_filtered[found_col].dropna().unique() if str(x) != 'nan'])
            if len(values) > 1:
                selected = st.sidebar.selectbox(label, values, key=f"f_{col}")
                if selected != 'Todos':
                    df_filtered = df_filtered[df_filtered[found_col].astype(str) == selected]
    
    st.sidebar.markdown(f"**Registros:** {len(df_filtered):,}/{len(df):,}")
    if st.sidebar.button("🔄 Limpiar"):
        st.rerun()
    
    return df_filtered



def create_horizontal_bar_chart(necesidades_counts):
    """Crea gráfico de barras horizontales con prioridades - Top 6 + Otros"""
    
    # Tomar solo las top 6 necesidades
    top_6 = necesidades_counts.head(6)
    
    # Calcular "Otros" si hay más de 6 necesidades
    if len(necesidades_counts) > 6:
        otros_count = necesidades_counts.iloc[6:].sum()
        # Crear nueva serie con Top 6 + Otros
        chart_data = pd.concat([top_6, pd.Series([otros_count], index=['Otros'])])
    else:
        chart_data = top_6
    
    # Colores por prioridad
    total = necesidades_counts.sum()
    colors = []
    
    for i, (name, count) in enumerate(chart_data.items()):
        if name == 'Otros':
            colors.append('#757575')  # Gris para "Otros"
        else:
            pct = (count / total) * 100
            if pct >= 10:
                colors.append('#F44336')  # Rojo - Alta prioridad
            elif pct >= 3:
                colors.append('#FF9800')  # Naranja - Media prioridad
            else:
                colors.append('#FFC107')  # Amarillo - Baja prioridad
    
    # Crear el gráfico
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=chart_data.index,
        x=chart_data.values,
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0.1)', width=1)),
        text=chart_data.values,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Menciones: %{x}<br>%{customdata:.1f}%<extra></extra>',
        customdata=[(c/total)*100 for c in chart_data.values]
    ))
    
    # Configuración del layout con título
    fig.update_layout(
        title={
            'text': "🎯 Top 6 Necesidades Más Críticas + Otros", 
            'x': 0.5, 
            'font': {'size': 18, 'color': '#D32F2F'}
        },
        xaxis_title="Número de Menciones", 
        yaxis_title="Necesidades Identificadas",
        height=400,  # Altura fija para 7 elementos máximo (Top 6 + Otros)
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=80, t=60, b=40)
    )
    
    # Configurar ejes para orden descendente
    fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=False, autorange="reversed")  # Orden descendente
    
    return fig
    """Crea gráfico de barras horizontales con prioridades - Top 6 + Otros"""
    
    # Tomar solo las top 6 necesidades
    top_6 = necesidades_counts.head(6)
    
    # Calcular "Otros" si hay más de 6 necesidades
    if len(necesidades_counts) > 6:
        otros_count = necesidades_counts.iloc[6:].sum()
        # Crear nueva serie con Top 6 + Otros
        chart_data = pd.concat([top_6, pd.Series([otros_count], index=['Otros'])])
    else:
        chart_data = top_6
    
    # Colores por prioridad
    total = necesidades_counts.sum()
    colors = []
    
    for i, (name, count) in enumerate(chart_data.items()):
        if name == 'Otros':
            colors.append('#757575')  # Gris para "Otros"
        else:
            pct = (count / total) * 100
            if pct >= 10:
                colors.append('#F44336')  # Rojo - Alta prioridad
            elif pct >= 3:
                colors.append('#FF9800')  # Naranja - Media prioridad
            else:
                colors.append('#FFC107')  # Amarillo - Baja prioridad
    
    # Crear el gráfico
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=chart_data.index,
        x=chart_data.values,
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0.1)'))))
    fig.update_yaxes(showgrid=False, autorange="reversed")
    
    return fig
                                            
def create_summary_table(necesidades_counts):
    """Crea tabla resumen con prioridades"""
    total = necesidades_counts.sum()
    priorities = []
    
    for count in necesidades_counts.values:
        pct = (count / total) * 100
        if pct >= 10:
            priorities.append('🔴 Alta')
        elif pct >= 3:
            priorities.append('🟡 Media')
        else:
            priorities.append('⚪ Baja')
    
    return pd.DataFrame({
        'Necesidad': necesidades_counts.index,
        'Menciones': necesidades_counts.values,
        'Porcentaje': [f"{(c/total)*100:.1f}%" for
                       c in necesidades_counts.values],
        'Prioridad': priorities,
        'Ranking': range(1, len(necesidades_counts) + 1)
    })

def main():
    # Header
    st.markdown('<div class="page-header">🎯 Necesidades</div>', unsafe_allow_html=True)
    
    # Cargar datos
    with st.spinner('🔄 Cargando datos...'):
        df = load_data_from_sheets() if modules_loaded else None
    
    if df is None:
        st.error("❌ No se pudieron cargar los datos")
        return
    
    # Info básica
    st.markdown(f"""
    <div class="metric-container">
        <h4>📊 Sistema Operativo</h4>
        <p><strong>Registros:</strong> {len(df):,} | <strong>Actualización:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros y análisis
    df_filtered = create_filters_sidebar(df)
    necesidades_counts, necesidades_col, analysis_text = analyze_necesidades(df_filtered)
    
    if necesidades_counts is None:
        st.error("❌ No se pudo analizar la columna de necesidades")
        if analysis_text:
            st.info(analysis_text)
        return
    
    # Pestañas
    tab1, tab2 = st.tabs(["📊 Gráfico de Barras", "📋 Análisis Detallado"])
    
    with tab1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Menciones", f"{necesidades_counts.sum():,}")
        with col2:
            st.metric("Necesidades Únicas", f"{len(necesidades_counts)}")
        with col3:
            high, medium, low = categorize_necesidades(necesidades_counts)
            st.metric("Alta Prioridad", f"{len(high)}")
        with col4:
            principal_pct = (necesidades_counts.iloc[0] / necesidades_counts.sum()) * 100 if len(necesidades_counts) > 0 else 0
            st.metric("Necesidad Principal", f"{principal_pct:.1f}%")
        
        st.markdown("---")
        
        # Gráfico de barras Top 18
        if not necesidades_counts.empty:
            bar_fig = create_horizontal_bar_chart(necesidades_counts)
            st.plotly_chart(bar_fig, use_container_width=True)
            
            # Leyenda de colores
            st.markdown("""
            **Leyenda de Prioridades:**
            🔴 **Alta (≥10%)** | 🟡 **Media (3-10%)** | ⚪ **Baja (<3%)**
            """)
            
            # Tabla resumen
            st.markdown("### 📋 Tabla Completa")
            summary_df = create_summary_table(necesidades_counts)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Descarga
            csv = summary_df.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV", csv,
                file_name=f"necesidades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
        
        if analysis_text:
            st.markdown(analysis_text)
            
            if not necesidades_counts.empty:
                st.markdown("---")
                
                # Análisis por prioridades
                st.markdown("### 🎯 Análisis por Prioridades")
                
                high, medium, low = categorize_necesidades(necesidades_counts)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔴 Necesidades de Alta Prioridad:**")
                    for necesidad, count in list(high.items())[:5]:
                        pct = (count / necesidades_counts.sum()) * 100
                        st.markdown(f"""
                        <div class="priority-high">
                            <strong>{necesidad}:</strong> {count:,} ({pct:.1f}%)
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**🟡 Necesidades de Media Prioridad:**")
                    for necesidad, count in list(medium.items())[:5]:
                        pct = (count / necesidades_counts.sum()) * 100
                        st.markdown(f"""
                        <div class="priority-medium">
                            <strong>{necesidad}:</strong> {count:,} ({pct:.1f}%)
                        </div>
                        """, unsafe_allow_html=True)
                
                # Estadísticas
                st.markdown("### 📈 Estadísticas")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    mean_val, median_val = necesidades_counts.mean(), necesidades_counts.median()
                    st.markdown(f"""
                    <div class="highlight-stat"><strong>Media:</strong> {mean_val:.1f}</div>
                    <div class="highlight-stat"><strong>Mediana:</strong> {median_val:.1f}</div>
                    """, unsafe_allow_html=True)
                
                with col_b:
                    total = necesidades_counts.sum()
                    top5_pct = (necesidades_counts.head(5).sum() / total) * 100
                    st.markdown(f"""
                    <div class="highlight-stat"><strong>Top 5:</strong> {top5_pct:.1f}%</div>
                    <div class="highlight-stat"><strong>Diversidad:</strong> {len(necesidades_counts)} tipos</div>
                    """, unsafe_allow_html=True)
                
                # Recomendaciones
                st.markdown("### 💡 Recomendaciones")
                
                if len(high) > 0:
                    st.error(f"🚨 **Atención inmediata:** {len(high)} necesidades de alta prioridad requieren acción urgente")
                
                if len(necesidades_counts) > 25:
                    st.info("📌 **Muchas necesidades:** Considerar agrupar necesidades similares para mejor gestión")
                
                coverage_rate = len(df_filtered[necesidades_col].dropna()) / len(df_filtered) * 100
                if coverage_rate < 80:
                    st.warning(f"⚠️ **Cobertura baja:** Solo {coverage_rate:.1f}% de comedores tienen necesidades documentadas")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()