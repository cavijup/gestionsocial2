import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# Importar pywaffle con manejo de errores
try:
    from pywaffle import Waffle
    waffle_available = True
except ImportError:
    waffle_available = False

# Importar módulos locales
try:
    from utils.google_sheets import load_data_from_sheets
    modules_loaded = True
except ImportError:
    modules_loaded = False

# Configuración básica
st.set_page_config(page_title="🔍 Cruce de Variables", page_icon="🔍", layout="wide")

# CSS compacto
st.markdown("""
<style>
.page-header {font-size: 2.2rem; font-weight: bold; color: #1565C0; text-align: center; 
             margin-bottom: 1.5rem; padding: 1rem; background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%); border-radius: 10px;}
.metric-container, .chart-container, .variable-selector, .insight-box, .grouping-info, .waffle-info {
    padding: 1rem; border-radius: 8px; margin: 1rem 0; background-color: #f8f9fa;}
.variable-selector {background-color: #FFF8E1; border-left: 4px solid #FFB300;}
.insight-box {background-color: #E8F5E8; border-left: 4px solid #4CAF50;}
.grouping-info {background-color: #E3F2FD; border-left: 4px solid #1976D2;}
.waffle-info {background-color: #FFF3E0; border-left: 4px solid #FF9800;}
</style>
""", unsafe_allow_html=True)

# Mapeo de columnas
COLUMN_MAPPING = {
    'acciones_aparte': '¿El comedor realiza otras acciones aparte de la preparación y entrega de raciones?',
    'frecuencia_actividades': '¿Con que frecuencia realiza estas actividades y/o procesos?',
    'temas_ejecutados': 'TEMAS O ACTIVIDADES QUE SE HAN EJECUTADO ANTERIORMENTE',
    'articulacion_institucion': 'Para el desarrollo de actividades ¿El comedor se ha articulado con alguna institución?',
    'sector_articulacion': 'De qué sector',
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
        'sector_articulacion': ['De qué sector', 'sector'],
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

def clean_and_group_data(series, top_n=8):
    """Limpia y agrupa datos categóricos"""
    if series is None or series.empty: return series
    
    # Limpiar datos
    cleaned = series.astype(str).str.strip().replace(['nan', 'None', '', 'NaN'], 'Sin respuesta')
    cleaned = cleaned.replace({'Si': 'Sí', 'si': 'Sí', 'SI': 'Sí', 'No': 'No', 'no': 'No', 'NO': 'No'})
    
    # Agrupar top N
    value_counts = cleaned.value_counts()
    if len(value_counts) <= top_n: return cleaned
    
    top_categories = value_counts.head(top_n).index.tolist()
    return cleaned.apply(lambda x: x if x in top_categories else 'Otros')

def create_waffle_chart(df, var1, var2, var1_name, var2_name):
    """Crea gráfico waffle mejorado y más atractivo"""
    if not waffle_available:
        return None, "pywaffle no está instalado"
    
    # Preparar datos (Top 6 para waffle)
    data1 = clean_and_group_data(df[var1], top_n=6)
    data2 = clean_and_group_data(df[var2], top_n=6)
    crosstab = pd.crosstab(data1, data2)
    total = crosstab.sum().sum()
    
    # Crear combinaciones
    combinations = []
    for var1_cat in crosstab.index:
        for var2_cat in crosstab.columns:
            count = crosstab.loc[var1_cat, var2_cat]
            if count > 0:
                percentage = round((count / total) * 100)
                if percentage >= 1:
                    # Acortar etiquetas para mejor legibilidad
                    label1 = var1_cat[:20] + "..." if len(var1_cat) > 20 else var1_cat
                    label2 = var2_cat[:20] + "..." if len(var2_cat) > 20 else var2_cat
                    combinations.append((f"{label1} × {label2}", percentage, count))
    
    combinations.sort(key=lambda x: x[1], reverse=True)
    combinations = combinations[:8]  # Reducir a 8 para mejor visualización
    
    if not combinations:
        return None, "No hay combinaciones suficientemente frecuentes"
    
    # 🎨 CAMBIA AQUÍ LOS COLORES DE LOS CUADRITOS
    # Opción 1: Colores modernos (actual)
    modern_colors = [
        '#FF6B8A',  # Rosa vibrante
        '#4ECDC4',  # Turquesa
        '#45B7D1',  # Azul cielo
        '#96CEB4',  # Verde menta
        '#FFEAA7',  # Amarillo suave
        '#A29BFE',  # Púrpura claro
        '#74B9FF',  # Azul claro
        '#FD79A8',  # Rosa suave
        '#6C5CE7',  # Púrpura
        '#00B894',  # Verde esmeralda
        '#FDCB6E',  # Naranja suave
        '#E17055'   # Coral
    ]
    
    # Opción 2: Colores corporativos (descomenta para usar)
    # modern_colors = [
    #     '#1f77b4',  # Azul
    #     '#ff7f0e',  # Naranja
    #     '#2ca02c',  # Verde
    #     '#d62728',  # Rojo
    #     '#9467bd',  # Púrpura
    #     '#8c564b',  # Marrón
    #     '#e377c2',  # Rosa
    #     '#7f7f7f',  # Gris
    #     '#bcbd22',  # Verde oliva
    #     '#17becf',  # Cian
    #     '#ffbb78',  # Durazno
    #     '#98df8a'   # Verde claro
    # ]
    
    # Opción 3: Colores pasteles (descomenta para usar)
    # modern_colors = [
    #     '#FFB3BA',  # Rosa pastel
    #     '#FFDFBA',  # Durazno pastel
    #     '#FFFFBA',  # Amarillo pastel
    #     '#BAFFC9',  # Verde pastel
    #     '#BAE1FF',  # Azul pastel
    #     '#D4BAFF',  # Púrpura pastel
    #     '#FFB3E6',  # Magenta pastel
    #     '#B3FFB3',  # Lima pastel
    #     '#FFE6B3',  # Beige pastel
    #     '#E6B3FF',  # Lavanda pastel
    #     '#B3E6FF',  # Celeste pastel
    #     '#FFCCB3'   # Coral pastel
    # ]
    
    # Preparar datos para waffle con etiquetas mejoradas
    labels = []
    values = []
    colors = []
    
    for i, combo in enumerate(combinations):
        # Etiquetas más limpias y legibles
        label = f"{combo[0]}\n{combo[1]}% ({combo[2]:,})"
        labels.append(label)
        values.append(combo[1])
        colors.append(modern_colors[i % len(modern_colors)])
    
    # Ajustar para 100%
    total_pct = sum(values)
    if total_pct < 100:
        remainder = 100 - total_pct
        if remainder >= 2:  # Solo mostrar si es significativo
            labels.append(f"Otras combinaciones\n{remainder}%")
            values.append(remainder)
            colors.append('#BDC3C7')  # Gris suave
    
    try:
        # Configuración mejorada del waffle
        fig = plt.figure(
            figsize=(18, 12),  # Tamaño más grande
            FigureClass=Waffle,
            rows=10,
            columns=10,
            values=values,
            labels=labels,
            colors=colors,
            legend={
                'loc': 'center', 
                'bbox_to_anchor': (0.5, -0.1),
                'ncol': 3,  # 3 columnas para mejor distribución
                'fontsize': 16,  # 🔤 TAMAÑO DE ETIQUETAS DE LEYENDA - AUMENTADO (era 14)
                'frameon': False,
                'columnspacing': 2.0,  # 📏 Aumentado espacio entre columnas para letras más grandes
                'handletextpad': 1.2   # 📏 Aumentado espacio entre color y texto
            },
            starting_location='NW',
            block_arranging_style='snake',
            rounding_rule='ceil',  # Redondeo hacia arriba
            plot_anchor='C'  # Centrar el plot
        )
        
        # 🎯 TÍTULOS - Tamaños de fuente
        plt.suptitle(
            f'Análisis de Cruce de Variables\n{var1_name} × {var2_name}', 
            fontsize=20,        # 🔤 TAMAÑO TÍTULO PRINCIPAL (14-24)
            fontweight='bold', 
            y=0.95,
            color='#2C3E50'  # Color azul oscuro elegante
        )
        
        # 📍 CAMBIA AQUÍ LA POSICIÓN DEL SUBTÍTULO
        # Valores Y: 0.0 = abajo, 1.0 = arriba
        plt.figtext(
            0.5,        # X: 0.5 = centro horizontal
            0.88,       # Y: Cambia este valor para mover arriba/abajo
            'Cada cuadrito representa ≈ 1% del total de casos analizados',
            ha='center',    # Alineación horizontal: 'center', 'left', 'right'
            va='center',    # Alineación vertical: 'center', 'top', 'bottom'
            fontsize=13,    # 🔤 TAMAÑO SUBTÍTULO (10-16)
            style='italic',
            color='#7F8C8D'  # Gris medio
        )
        
        # Mejorar el fondo
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1.0)
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25, top=0.85)  # Más espacio para leyenda y títulos
        
        return fig, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def analyze_association(crosstab, original_var1_count, original_var2_count):
    """Analiza asociación entre variables"""
    max_cell = crosstab.max().max()
    max_positions = np.where(crosstab.values == max_cell)
    total = crosstab.sum().sum()
    
    if len(max_positions[0]) > 0:
        max_row = crosstab.index[max_positions[0][0]]
        max_col = crosstab.columns[max_positions[1][0]]
        
        has_otros_var1 = 'Otros' in crosstab.index
        has_otros_var2 = 'Otros' in crosstab.columns
        
        insights = f"""### 🔍 Insights del Cruce
**Combinación más frecuente:** {max_row} + {max_col}: {max_cell} casos ({(max_cell/total)*100:.1f}%)
**Total casos:** {total:,} | **Combinaciones:** {(crosstab > 0).sum().sum()}
**Categorías:** Var1: {len(crosstab.index)}/{original_var1_count} | Var2: {len(crosstab.columns)}/{original_var2_count}"""
        
        if has_otros_var1 or has_otros_var2:
            insights += "\n\n**📊 Agrupación aplicada:**"
            if has_otros_var1:
                otros_count = crosstab.loc['Otros'].sum()
                insights += f"\n- Variable 1: {original_var1_count - len(crosstab.index) + 1} categorías en 'Otros' ({otros_count:,} casos)"
            if has_otros_var2:
                otros_count = crosstab['Otros'].sum()
                insights += f"\n- Variable 2: {original_var2_count - len(crosstab.columns) + 1} categorías en 'Otros' ({otros_count:,} casos)"
        
        return insights
    return "No se pudieron generar insights automáticos."

def main():
    # Header
    st.markdown('<div class="page-header">🔍 Cruce de Variables Cualitativas</div>', unsafe_allow_html=True)
    
    if not waffle_available:
        st.warning("⚠️ pywaffle no disponible. Ejecuta: `pip install pywaffle`")
    
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
    
    # Info de agrupación
    st.markdown("""<div class="grouping-info">
    <h4>ℹ️ Agrupación Automática</h4>
    <p>Las variables se limitan a sus <strong>8 categorías más frecuentes</strong> (6 para Waffle). 
    Las restantes se agrupan en <strong>"Otros"</strong>.</p>
    </div>""", unsafe_allow_html=True)
    
    # Obtener columnas disponibles
    available_columns = get_available_columns(df)
    if not available_columns:
        st.error("❌ Columnas no encontradas")
        st.info("**Columnas disponibles:**")
        st.write(list(df.columns))
        return
    
    # Selectores
    st.markdown('<div class="variable-selector">### 🎯 Selección de Variables</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        var1_key = st.selectbox("**Variable 1 (Filas):**", list(available_columns.keys()),
                               format_func=lambda x: COLUMN_MAPPING.get(x, x))
    with col2:
        var2_options = [k for k in available_columns.keys() if k != var1_key]
        var2_key = st.selectbox("**Variable 2 (Columnas):**", var2_options,
                               format_func=lambda x: COLUMN_MAPPING.get(x, x))
    
    if var1_key and var2_key:
        var1_col, var2_col = available_columns[var1_key], available_columns[var2_key]
        var1_name, var2_name = COLUMN_MAPPING.get(var1_key, var1_key), COLUMN_MAPPING.get(var2_key, var2_key)
        
        # Filtrar datos válidos
        df_clean = df[[var1_col, var2_col]].dropna()
        if df_clean.empty:
            st.warning("⚠️ No hay datos válidos")
            return
        
        # Conteos originales
        original_var1_count = df_clean[var1_col].astype(str).str.strip().replace(['nan', 'None', '', 'NaN'], 'Sin respuesta').nunique()
        original_var2_count = df_clean[var2_col].astype(str).str.strip().replace(['nan', 'None', '', 'NaN'], 'Sin respuesta').nunique()
        
        # Visualización Waffle única
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if waffle_available:
            st.markdown("### 🧇 Análisis Visual Interactivo")
            
            # Info box mejorada
            st.markdown("""
            <div class="waffle-info">
                <strong>🎯 Interpretación:</strong> Cada cuadrito representa ≈1% del total. 
                Las combinaciones más frecuentes aparecen con colores más vibrantes.
                <br><strong>📊 Datos:</strong> Se muestran las 8 combinaciones principales de variables.
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("🎨 Creando visualización waffle..."):
                waffle_fig, error_msg = create_waffle_chart(df_clean, var1_col, var2_col, var1_name, var2_name)
            
            if waffle_fig:
                st.pyplot(waffle_fig, use_container_width=True)
                
                # Métricas adicionales con mejor diseño
                col1, col2, col3, col4 = st.columns(4)
                total_cases = len(df_clean)
                
                with col1:
                    st.metric("📊 Total Casos", f"{total_cases:,}")
                with col2:
                    st.metric("🔀 Var1 Categorías", f"{clean_and_group_data(df_clean[var1_col], 6).nunique()}")
                with col3:
                    st.metric("🔀 Var2 Categorías", f"{clean_and_group_data(df_clean[var2_col], 6).nunique()}")
                with col4:
                    valid_combinations = pd.crosstab(
                        clean_and_group_data(df_clean[var1_col], 6),
                        clean_and_group_data(df_clean[var2_col], 6)
                    )
                    st.metric("🎯 Combinaciones", f"{(valid_combinations > 0).sum().sum()}")
                
                plt.close(waffle_fig)
            elif error_msg:
                st.error(f"❌ {error_msg}")
                st.info("💡 **Sugerencia:** Prueba con variables que tengan distribuciones más balanceadas")
        else:
            st.error("❌ pywaffle no disponible")
            st.code("pip install pywaffle", language="bash")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()