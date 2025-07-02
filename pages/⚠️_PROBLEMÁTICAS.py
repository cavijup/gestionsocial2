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
    page_title="⚠️ Problemáticas",
    page_icon="⚠️",
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
        color: #E65100;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #FFF3E0 0%, #FFE0B2 100%);
        border-radius: 10px;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #E65100;
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
        background-color: #FFF3E0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #E65100;
        margin: 1rem 0;
    }
    .highlight-stat {
        background-color: #E8F5E8;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #4CAF50;
    }
    .severity-critical {
        background-color: #FFEBEE;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #F44336;
    }
    .severity-high {
        background-color: #FFF3E0;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #FF9800;
    }
    .severity-medium {
        background-color: #FFFDE7;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #FFC107;
    }
</style>
""", unsafe_allow_html=True)

def find_problematicas_column(df):
    """Busca la columna de problemáticas"""
    if df is None:
        return None
    
    possible_names = ['PROBLEMÁTICAS', 'PROBLEMATICAS', 'PROBLEMAS', 'DIFICULTADES', 'OBSTÁCULOS']
    
    # Buscar exacto
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Buscar parcial
    for col in df.columns:
        if 'problem' in col.lower():
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

def categorize_problematicas(problematicas_counts):
    """Categoriza problemáticas por nivel de severidad"""
    total = problematicas_counts.sum()
    critical = {}    # ≥15%
    high = {}        # 8-15%
    medium = {}      # 3-8%
    low = {}         # <3%
    
    for problematica, count in problematicas_counts.items():
        percentage = (count / total) * 100
        if percentage >= 15:
            critical[problematica] = count
        elif percentage >= 8:
            high[problematica] = count
        elif percentage >= 3:
            medium[problematica] = count
        else:
            low[problematica] = count
    
    return critical, high, medium, low

def analyze_problematicas(df):
    """Analiza las problemáticas identificadas"""
    if df is None or df.empty:
        return None, None, None
    
    problematicas_col = find_problematicas_column(df)
    if not problematicas_col:
        return None, None, "❌ No se encontró la columna 'PROBLEMÁTICAS'"
    
    valid_data = df[problematicas_col].dropna()
    if valid_data.empty:
        return None, None, "⚠️ No hay datos válidos en la columna de problemáticas"
    
    all_problematicas = parse_multiple_options(valid_data)
    if not all_problematicas:
        return None, None, "⚠️ No se pudieron extraer problemáticas válidas"
    
    problematicas_counts = pd.Series(all_problematicas).value_counts()
    total_menciones = len(all_problematicas)
    comedores_con_problematicas = len(valid_data)
    total_comedores = len(df)
    
    # Categorizar por severidad
    critical, high, medium, low = categorize_problematicas(problematicas_counts)
    
    # Análisis textual
    analysis_text = f"""
## ⚠️ Análisis de Problemáticas Identificadas

**Resumen:**
- **Total comedores:** {total_comedores:,}
- **Con problemáticas definidas:** {comedores_con_problematicas:,} ({(comedores_con_problematicas/total_comedores)*100:.1f}%)
- **Total menciones:** {total_menciones:,}
- **Problemáticas únicas:** {len(problematicas_counts)}
- **Promedio por comedor:** {total_menciones/comedores_con_problematicas:.1f}

**Clasificación por Severidad:**
- **🔴 Críticas (≥15%):** {len(critical)} problemáticas
- **🟠 Altas (8-15%):** {len(high)} problemáticas
- **🟡 Medias (3-8%):** {len(medium)} problemáticas
- **⚪ Bajas (<3%):** {len(low)} problemáticas

**Top 8 Problemáticas Más Frecuentes:**
"""
    
    for problematica, count in problematicas_counts.head(8).items():
        percentage = (count / total_menciones) * 100
        if percentage >= 15:
            severity = "🔴"
        elif percentage >= 8:
            severity = "🟠"
        elif percentage >= 3:
            severity = "🟡"
        else:
            severity = "⚪"
        analysis_text += f"\n- {severity} **{problematica}:** {count:,} ({percentage:.1f}%)"
    
    return problematicas_counts, problematicas_col, analysis_text

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

def create_horizontal_bar_chart(problematicas_counts):
    """Crea gráfico de barras horizontales con severidades - Top 7 + Otros"""
    
    # Tomar solo las top 7 problemáticas
    top_7 = problematicas_counts.head(7)
    
    # Calcular "Otros" si hay más de 7 problemáticas
    if len(problematicas_counts) > 7:
        otros_count = problematicas_counts.iloc[7:].sum()
        # Crear nueva serie con Top 7 + Otros
        chart_data = pd.concat([top_7, pd.Series([otros_count], index=['Otros'])])
    else:
        chart_data = top_7
    
    # Colores por severidad
    total = problematicas_counts.sum()
    colors = []
    
    for i, (name, count) in enumerate(chart_data.items()):
        if name == 'Otros':
            colors.append('#757575')  # Gris para "Otros"
        else:
            pct = (count / total) * 100
            if pct >= 15:
                colors.append('#D32F2F')  # Rojo - Crítica
            elif pct >= 8:
                colors.append('#F57C00')  # Naranja - Alta
            elif pct >= 3:
                colors.append('#FBC02D')  # Amarillo - Media
            else:
                colors.append('#9E9E9E')  # Gris - Baja
    
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
    
    fig.update_layout(
        title={'text': "⚠️ Top 7 Problemáticas + Otros", 'x': 0.5, 'font': {'size': 18, 'color': '#E65100'}},
        xaxis_title="Número de Menciones", 
        yaxis_title="Problemáticas Identificadas",
        height=450,  # Altura fija para 8 elementos máximo (Top 7 + Otros)
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=80, t=60, b=40)
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=False, autorange="reversed")
    
    return fig       # Tomar solo las top 8 problemáticas
    top_8 = problematicas_counts.head(8)
    
    # Calcular "Otros" si hay más de 8 problemáticas
    if len(problematicas_counts) > 8:
        otros_count = problematicas_counts.iloc[8:].sum()
        # Crear nueva serie con Top 8 + Otros
        chart_data = pd.concat([top_8, pd.Series([otros_count], index=['Otros'])])
    else:
        chart_data = top_8
    
    # Colores por severidad
    total = problematicas_counts.sum()
    colors = []
    
    for i, (name, count) in enumerate(chart_data.items()):
        if name == 'Otros':
            colors.append('#757575')  # Gris para "Otros"
        else:
            pct = (count / total) * 100
            if pct >= 15:
                colors.append('#D32F2F')  # Rojo - Crítica
            elif pct >= 8:
                colors.append('#F57C00')  # Naranja - Alta
            elif pct >= 3:
                colors.append('#FBC02D')  # Amarillo - Media
            else:
                colors.append('#9E9E9E')  # Gris - Baja
    
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
    
    fig.update_layout(
        title={'text': "⚠️ Top 8 Problemáticas + Otros", 'x': 0.5, 'font': {'size': 18, 'color': '#E65100'}},
        xaxis_title="Número de Menciones", 
        yaxis_title="Problemáticas Identificadas",
        height=500,  # Altura fija para 9 elementos máximo
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=80, t=60, b=40)
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=False, autorange="reversed")
    
    return fig

def create_summary_table(problematicas_counts):
    """Crea tabla resumen con severidades"""
    total = problematicas_counts.sum()
    severities = []
    
    for count in problematicas_counts.values:
        pct = (count / total) * 100
        if pct >= 15:
            severities.append('🔴 Crítica')
        elif pct >= 8:
            severities.append('🟠 Alta')
        elif pct >= 3:
            severities.append('🟡 Media')
        else:
            severities.append('⚪ Baja')
    
    return pd.DataFrame({
        'Problemática': problematicas_counts.index,
        'Menciones': problematicas_counts.values,
        'Porcentaje': [f"{(c/total)*100:.1f}%" for c in problematicas_counts.values],
        'Severidad': severities,
        'Ranking': range(1, len(problematicas_counts) + 1)
    })

def main():
    # Header
    st.markdown('<div class="page-header">⚠️ Problemáticas</div>', unsafe_allow_html=True)
    
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
    problematicas_counts, problematicas_col, analysis_text = analyze_problematicas(df_filtered)
    
    if problematicas_counts is None:
        st.error("❌ No se pudo analizar la columna de problemáticas")
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
            st.metric("Total Menciones", f"{problematicas_counts.sum():,}")
        with col2:
            st.metric("Problemáticas Únicas", f"{len(problematicas_counts)}")
        with col3:
            critical, high, medium, low = categorize_problematicas(problematicas_counts)
            st.metric("Críticas", f"{len(critical)}")
        with col4:
            principal_pct = (problematicas_counts.iloc[0] / problematicas_counts.sum()) * 100 if len(problematicas_counts) > 0 else 0
            st.metric("Principal", f"{principal_pct:.1f}%")
        
        st.markdown("---")
        
        # Gráfico de barras
        if not problematicas_counts.empty:
            bar_fig = create_horizontal_bar_chart(problematicas_counts)
            st.plotly_chart(bar_fig, use_container_width=True)
            
            # Leyenda de severidades
            st.markdown("""
            **Leyenda de Severidades:**
            🔴 **Crítica (≥15%)** | 🟠 **Alta (8-15%)** | 🟡 **Media (3-8%)** | ⚪ **Baja (<3%)**
            """)
            
            # Tabla resumen
            st.markdown("### 📋 Tabla Completa de Problemáticas")
            summary_df = create_summary_table(problematicas_counts)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Descarga
            csv = summary_df.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV", csv,
                file_name=f"problematicas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
        
        if analysis_text:
            st.markdown(analysis_text)
            
            if not problematicas_counts.empty:
                st.markdown("---")
                
                # Análisis por severidades
                st.markdown("### ⚠️ Análisis por Severidades")
                
                critical, high, medium, low = categorize_problematicas(problematicas_counts)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔴 Problemáticas Críticas:**")
                    if critical:
                        for problematica, count in list(critical.items())[:4]:
                            pct = (count / problematicas_counts.sum()) * 100
                            st.markdown(f"""
                            <div class="severity-critical">
                                <strong>{problematica}:</strong> {count:,} ({pct:.1f}%)
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("✅ No hay problemáticas críticas identificadas")
                    
                    st.markdown("**🟠 Problemáticas de Alta Severidad:**")
                    for problematica, count in list(high.items())[:3]:
                        pct = (count / problematicas_counts.sum()) * 100
                        st.markdown(f"""
                        <div class="severity-high">
                            <strong>{problematica}:</strong> {count:,} ({pct:.1f}%)
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**🟡 Problemáticas de Media Severidad:**")
                    for problematica, count in list(medium.items())[:4]:
                        pct = (count / problematicas_counts.sum()) * 100
                        st.markdown(f"""
                        <div class="severity-medium">
                            <strong>{problematica}:</strong> {count:,} ({pct:.1f}%)
                        </div>
                        """, unsafe_allow_html=True)
                
                # Estadísticas
                st.markdown("### 📈 Estadísticas y Concentración")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    mean_val, median_val = problematicas_counts.mean(), problematicas_counts.median()
                    st.markdown(f"""
                    <div class="highlight-stat"><strong>Media:</strong> {mean_val:.1f} menciones</div>
                    <div class="highlight-stat"><strong>Mediana:</strong> {median_val:.1f} menciones</div>
                    <div class="highlight-stat"><strong>Diversidad:</strong> {len(problematicas_counts)} tipos</div>
                    """, unsafe_allow_html=True)
                
                with col_b:
                    total = problematicas_counts.sum()
                    top3_pct = (problematicas_counts.head(3).sum() / total) * 100
                    top5_pct = (problematicas_counts.head(5).sum() / total) * 100
                    st.markdown(f"""
                    <div class="highlight-stat"><strong>Top 3:</strong> {top3_pct:.1f}% del total</div>
                    <div class="highlight-stat"><strong>Top 5:</strong> {top5_pct:.1f}% del total</div>
                    <div class="highlight-stat"><strong>Críticas + Altas:</strong> {len(critical) + len(high)} tipos</div>
                    """, unsafe_allow_html=True)
                
                # Recomendaciones y alertas
                st.markdown("### 🚨 Alertas y Recomendaciones")
                
                if len(critical) > 0:
                    st.error(f"🚨 **ATENCIÓN URGENTE:** {len(critical)} problemáticas críticas requieren intervención inmediata")
                
                if len(high) > 3:
                    st.warning(f"⚠️ **Alta preocupación:** {len(high)} problemáticas de alta severidad necesitan atención prioritaria")
                
                total_severe = len(critical) + len(high)
                if total_severe > len(problematicas_counts) * 0.3:
                    st.warning("⚠️ **Situación compleja:** Más del 30% de las problemáticas son de alta severidad")
                
                coverage_rate = len(df_filtered[problematicas_col].dropna()) / len(df_filtered) * 100
                if coverage_rate < 70:
                    st.info(f"📊 **Documentación:** {coverage_rate:.1f}% de comedores tienen problemáticas documentadas")
                
                if len(problematicas_counts) > 20:
                    st.info("📋 **Gestión:** Considerar agrupar problemáticas similares para mejor manejo")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()