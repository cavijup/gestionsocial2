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
    page_title="📋 Otras Categorías",
    page_icon="📋",
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
        color: #7B1FA2;
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: linear-gradient(90deg, #F3E5F5 0%, #E1BEE7 100%);
        border-radius: 10px;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #7B1FA2;
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
    .category-item {
        background-color: #F3E5F5;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border-left: 3px solid #7B1FA2;
    }
</style>
""", unsafe_allow_html=True)

def find_otras_categorias_column(df):
    """Busca la columna de otras categorías"""
    if df is None:
        return None
    
    possible_names = [
        'OTRAS CATEGORIAS',
        'OTRAS CATEGORIAS', 
        'OTRAS CATEGORIAS\r\n(Según su apreciación, indique cual es el tipo de población que en su mayoría se atiende en el comedor) Máximo 3 opciones',
        'OTRAS CATEGORIAS\r\n(Según su apreciación, indique cual es el tipo de población que en su mayoría se atiende en el comedor) Máximo 3 opciones'
    ]
    
    # Buscar exacto
    for name in possible_names:
        if name in df.columns:
            return name
    
    # Buscar parcial
    for col in df.columns:
        if 'otras' in col.lower() and 'categoria' in col.lower():
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

def analyze_otras_categorias(df):
    """Analiza las otras categorías poblacionales"""
    if df is None or df.empty:
        return None, None, None
    
    # Buscar la columna
    categorias_col = find_otras_categorias_column(df)
    if not categorias_col:
        return None, None, "❌ No se encontró la columna 'OTRAS CATEGORÍAS'"
    
    valid_data = df[categorias_col].dropna()
    if valid_data.empty:
        return None, None, "⚠️ No hay datos válidos en la columna de otras categorías"
    
    all_categorias = parse_multiple_options(valid_data)
    if not all_categorias:
        return None, None, "⚠️ No se pudieron extraer categorías válidas"
    
    categorias_counts = pd.Series(all_categorias).value_counts()
    total_menciones = len(all_categorias)
    comedores_con_categorias = len(valid_data)
    total_comedores = len(df)
    
    # Análisis textual conciso
    analysis_text = f"""
## 📋 Análisis de Otras Categorías Poblacionales

**Resumen:**
- **Total comedores:** {total_comedores:,}
- **Con categorías definidas:** {comedores_con_categorias:,} ({(comedores_con_categorias/total_comedores)*100:.1f}%)
- **Total menciones:** {total_menciones:,}
- **Categorías únicas:** {len(categorias_counts)}
- **Promedio por comedor:** {total_menciones/comedores_con_categorias:.1f}

**Top 8 Categorías:**
"""
    
    for categoria, count in categorias_counts.head(8).items():
        percentage = (count / total_menciones) * 100
        analysis_text += f"\n- **{categoria}:** {count:,} ({percentage:.1f}%)"
    
    if len(categorias_counts) > 0:
        principal = categorias_counts.index[0]
        principal_pct = (categorias_counts.iloc[0] / total_menciones) * 100
        analysis_text += f"\n\n**Insight:** {principal} es la categoría principal ({principal_pct:.1f}%)"
    
    return categorias_counts, categorias_col, analysis_text

def create_filters_sidebar(df):
    """Crea filtros en sidebar de forma compacta"""
    st.sidebar.markdown("### 🔍 Filtros")
    df_filtered = df.copy()
    
    # Columnas de filtro principales
    filters = {
        'NOMBRE DEL COMEDOR': '📍 Comedor',
        'BARRIO': '🏘️ Barrio', 
        'COMUNA': '🏛️ Comuna',
        'NODO ': '🔗 Nodo',
        'NICHO ': '🎯 Nicho'
    }
    
    applied = {}
    for col, label in filters.items():
        found_col = col if col in df.columns else next((c for c in df.columns if col.lower().replace(' ', '') in c.lower().replace(' ', '')), None)
        
        if found_col and found_col in df_filtered.columns:
            values = ['Todos'] + sorted([str(x) for x in df_filtered[found_col].dropna().unique() if str(x) != 'nan'])
            if len(values) > 1:
                selected = st.sidebar.selectbox(label, values, key=f"f_{col}")
                if selected != 'Todos':
                    df_filtered = df_filtered[df_filtered[found_col].astype(str) == selected]
                    applied[found_col] = selected
    
    st.sidebar.markdown(f"**Registros:** {len(df_filtered):,}/{len(df):,}")
    if st.sidebar.button("🔄 Limpiar"):
        st.rerun()
    
    return df_filtered

def create_horizontal_bar_chart(categorias_counts):
    """Crea gráfico de barras horizontales - Top 8 + Otros"""
    
    # Tomar solo las top 8 categorías
    top_8 = categorias_counts.head(8)
    
    # Calcular "Otros" si hay más de 8 categorías
    if len(categorias_counts) > 8:
        otros_count = categorias_counts.iloc[8:].sum()
        # Crear nueva serie con Top 8 + Otros
        chart_data = pd.concat([top_8, pd.Series([otros_count], index=['Otros'])])
    else:
        chart_data = top_8
    
    # Colores: degradado púrpura para las top 8 y gris para "Otros"
    colors = []
    base_colors = px.colors.sequential.Purples_r[:8]  # Solo 8 colores del degradado
    
    for i, (name, count) in enumerate(chart_data.items()):
        if name == 'Otros':
            colors.append('#757575')  # Gris para "Otros"
        else:
            colors.append(base_colors[i % len(base_colors)])
    
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
        customdata=[(c/categorias_counts.sum())*100 for c in chart_data.values]
    ))
    
    fig.update_layout(
        title={
            'text': "📋 Top 8 Otras Categorías + Otros", 
            'x': 0.5, 
            'font': {'size': 18, 'color': '#7B1FA2'}
        },
        xaxis_title="Número de Menciones", 
        yaxis_title="Categorías Poblacionales",
        height=450,  # Altura fija para máximo 9 elementos (Top 8 + Otros)
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=60, t=60, b=40)
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=False, autorange="reversed")  # Orden descendente
    
    return fig

def create_summary_table(categorias_counts):
    """Crea tabla resumen"""
    total = categorias_counts.sum()
    return pd.DataFrame({
        'Categoría Poblacional': categorias_counts.index,
        'Menciones': categorias_counts.values,
        'Porcentaje': [f"{(c/total)*100:.1f}%" for c in categorias_counts.values],
        'Ranking': range(1, len(categorias_counts) + 1)
    })

def main():
    # Header
    st.markdown('<div class="page-header">📋 Otras Categorías</div>', unsafe_allow_html=True)
    
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
    categorias_counts, categorias_col, analysis_text = analyze_otras_categorias(df_filtered)
    
    if categorias_counts is None:
        st.error("❌ No se pudo analizar la columna de otras categorías")
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
            st.metric("Total Menciones", f"{categorias_counts.sum():,}")
        with col2:
            st.metric("Categorías Únicas", f"{len(categorias_counts)}")
        with col3:
            principal_pct = (categorias_counts.iloc[0] / categorias_counts.sum()) * 100 if len(categorias_counts) > 0 else 0
            st.metric("Categoría Principal", f"{principal_pct:.1f}%")
        with col4:
            # Diversidad (categorías que suman 80%)
            cumsum_pct = (categorias_counts.cumsum() / categorias_counts.sum() * 100)
            diversidad = len(cumsum_pct[cumsum_pct <= 80]) + 1
            st.metric("Diversidad (80%)", f"{diversidad}")
        
        st.markdown("---")
        
        # Gráfico principal
        if not categorias_counts.empty:
            fig = create_horizontal_bar_chart(categorias_counts)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla resumen
            st.markdown("### 📋 Resumen")
            summary_df = create_summary_table(categorias_counts)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            
            # Descarga
            csv = summary_df.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV", csv,
                file_name=f"otras_categorias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
        
        if analysis_text:
            st.markdown(analysis_text)
            
            if not categorias_counts.empty:
                st.markdown("---")
                
                # Análisis estadístico compacto
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📈 Estadísticas:**")
                    mean_val, median_val, std_val = categorias_counts.mean(), categorias_counts.median(), categorias_counts.std()
                    st.markdown(f"""
                    <div class="highlight-stat"><strong>Media:</strong> {mean_val:.1f}</div>
                    <div class="highlight-stat"><strong>Mediana:</strong> {median_val:.1f}</div>
                    <div class="highlight-stat"><strong>Desv. estándar:</strong> {std_val:.1f}</div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**🎯 Concentración:**")
                    total = categorias_counts.sum()
                    top3_pct = (categorias_counts.head(3).sum() / total) * 100
                    top5_pct = (categorias_counts.head(5).sum() / total) * 100
                    
                    concentration = (categorias_counts / total) ** 2
                    hhi = concentration.sum()
                    
                    level = "🔴 Alta" if hhi > 0.25 else "🟡 Moderada" if hhi > 0.15 else "🟢 Baja"
                    
                    st.markdown(f"""
                    <div class="highlight-stat"><strong>Top 3:</strong> {top3_pct:.1f}%</div>
                    <div class="highlight-stat"><strong>Top 5:</strong> {top5_pct:.1f}%</div>
                    <div class="highlight-stat"><strong>Concentración:</strong> {level}</div>
                    """, unsafe_allow_html=True)
                
                # Categorías más frecuentes
                st.markdown("### 🏷️ Categorías Destacadas")
                for i, (cat, count) in enumerate(categorias_counts.head(6).items()):
                    pct = (count / categorias_counts.sum()) * 100
                    st.markdown(f"""
                    <div class="category-item">
                        <strong>{i+1}. {cat}:</strong> {count:,} menciones ({pct:.1f}%)
                    </div>
                    """, unsafe_allow_html=True)
                
                # Recomendaciones compactas
                st.markdown("### 💡 Insights")
                if len(categorias_counts) > 15:
                    st.info("📌 **Alta diversidad:** Considerar agrupar categorías similares")
                if categorias_counts.iloc[0] / categorias_counts.sum() > 0.4:
                    st.warning("⚠️ **Alta concentración:** Una categoría domina significativamente")
                if len(df_filtered) != len(df):
                    filtered_coverage = len(df_filtered[categorias_col].dropna()) / len(df_filtered) * 100
                    st.info(f"📊 **Cobertura filtrada:** {filtered_coverage:.1f}% tienen categorías definidas")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()