import pandas as pd
import numpy as np
from collections import Counter
import re

def analyze_tipo_comedor(df):
    """
    Analiza la distribución de tipos de comedores
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        tuple: (tipo_counts, analysis_text) - Conteos y análisis textual
    """
    if df is None or df.empty:
        return None, None
    
    # Verificar que existe la columna
    if 'TIPO DE COMEDOR' not in df.columns:
        return None, "❌ La columna 'TIPO DE COMEDOR' no se encontró en los datos"
    
    # Contar valores en TIPO DE COMEDOR (excluyendo valores nulos)
    tipo_counts = df['TIPO DE COMEDOR'].dropna().value_counts()
    
    if tipo_counts.empty:
        return None, "⚠️ No hay datos válidos en la columna 'TIPO DE COMEDOR'"
    
    # Calcular porcentajes
    tipo_percentages = (tipo_counts / len(df.dropna(subset=['TIPO DE COMEDOR']))) * 100
    
    # Crear análisis textual
    total_comedores = len(df.dropna(subset=['TIPO DE COMEDOR']))
    tipos_disponibles = list(tipo_counts.index)
    
    analysis_text = f"""
## 📊 Análisis de Tipos de Comedores

**Resumen General:**
- **Total de comedores registrados:** {total_comedores:,}
- **Tipos identificados:** {len(tipos_disponibles)}
- **Registros con datos válidos:** {total_comedores:,} de {len(df):,} ({(total_comedores/len(df)*100):.1f}%)

**Distribución por tipo:**
"""
    
    for tipo, count in tipo_counts.items():
        percentage = (count / total_comedores) * 100
        analysis_text += f"\n- **{tipo}:** {count:,} comedores ({percentage:.1f}%)"
    
    # Agregar insights adicionales
    if len(tipo_counts) > 0:
        tipo_mas_comun = tipo_counts.index[0]
        analysis_text += f"""

**Insights clave:**
- El tipo más común es: **{tipo_mas_comun}**
- Representa el {tipo_percentages.iloc[0]:.1f}% del total de comedores
"""
        
        if len(tipo_counts) > 1:
            segundo_tipo = tipo_counts.index[1]
            analysis_text += f"\n- El segundo tipo más común es: **{segundo_tipo}** ({tipo_percentages.iloc[1]:.1f}%)"
        
        # Agregar análisis de diversidad
        if len(tipo_counts) > 2:
            analysis_text += f"\n- Los 3 tipos principales representan el {tipo_percentages.iloc[:3].sum():.1f}% del total"
    
    return tipo_counts, analysis_text

def analyze_geographic_distribution(df):
    """
    Analiza la distribución geográfica de los comedores
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        dict: Análisis geográfico por comuna, barrio, nodo y nicho
    """
    if df is None or df.empty:
        return None
    
    analysis = {}
    
    # Análisis por Comuna
    if 'COMUNA' in df.columns:
        comuna_counts = df['COMUNA'].dropna().value_counts()
        analysis['comunas'] = {
            'counts': comuna_counts,
            'total': len(comuna_counts),
            'mas_comedores': comuna_counts.index[0] if len(comuna_counts) > 0 else None,
            'max_count': comuna_counts.iloc[0] if len(comuna_counts) > 0 else 0
        }
    
    # Análisis por Barrio
    if 'BARRIO' in df.columns:
        barrio_counts = df['BARRIO'].dropna().value_counts()
        analysis['barrios'] = {
            'counts': barrio_counts,
            'total': len(barrio_counts),
            'mas_comedores': barrio_counts.index[0] if len(barrio_counts) > 0 else None,
            'max_count': barrio_counts.iloc[0] if len(barrio_counts) > 0 else 0
        }
    
    # Análisis por Nodo
    if 'NODO ' in df.columns:
        nodo_counts = df['NODO '].dropna().value_counts()
        analysis['nodos'] = {
            'counts': nodo_counts,
            'total': len(nodo_counts),
            'mas_comedores': nodo_counts.index[0] if len(nodo_counts) > 0 else None,
            'max_count': nodo_counts.iloc[0] if len(nodo_counts) > 0 else 0
        }
    
    # Análisis por Nicho
    if 'NICHO ' in df.columns:
        nicho_counts = df['NICHO '].dropna().value_counts()
        analysis['nichos'] = {
            'counts': nicho_counts,
            'total': len(nicho_counts),
            'mas_comedores': nicho_counts.index[0] if len(nicho_counts) > 0 else None,
            'max_count': nicho_counts.iloc[0] if len(nicho_counts) > 0 else 0
        }
    
    return analysis

def analyze_temporal_trends(df):
    """
    Analiza las tendencias temporales de vinculación de comedores
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        dict: Análisis temporal
    """
    if df is None or df.empty:
        return None
    
    if 'AÑO DE VINCULACIÓN AL PROGRAMA' not in df.columns:
        return None
    
    # Limpiar y convertir años
    años_serie = pd.to_numeric(df['AÑO DE VINCULACIÓN AL PROGRAMA'], errors='coerce').dropna()
    
    if años_serie.empty:
        return None
    
    años_counts = años_serie.value_counts().sort_index()
    
    analysis = {
        'años_counts': años_counts,
        'año_inicio': int(años_serie.min()),
        'año_fin': int(años_serie.max()),
        'período_activo': int(años_serie.max() - años_serie.min() + 1),
        'año_más_activo': int(años_counts.idxmax()),
        'comedores_año_más_activo': int(años_counts.max()),
        'promedio_anual': años_counts.mean(),
        'tendencia': 'creciente' if años_counts.iloc[-1] > años_counts.iloc[0] else 'decreciente'
    }
    
    return analysis

def analyze_population_focus(df):
    """
    Analiza el enfoque poblacional de los comedores
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        dict: Análisis de enfoques poblacionales
    """
    if df is None or df.empty:
        return None
    
    analysis = {}
    
    # Analizar enfoques diferenciales/étnicos
    if 'ENFOQUES DIFERENCIALES/ETNICOS\r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)' in df.columns:
        col_name = 'ENFOQUES DIFERENCIALES/ETNICOS\r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)'
        enfoques_data = df[col_name].dropna()
        
        # Separar múltiples opciones y contar
        all_enfoques = []
        for entry in enfoques_data:
            if pd.isna(entry) or entry == '':
                continue
            # Dividir por comas y limpiar
            enfoques = [e.strip() for e in str(entry).split(',')]
            all_enfoques.extend(enfoques)
        
        enfoques_counts = pd.Series(all_enfoques).value_counts()
        analysis['enfoques_diferenciales'] = {
            'counts': enfoques_counts,
            'total_menciones': len(all_enfoques),
            'comedores_con_enfoque': len(enfoques_data),
            'mas_comun': enfoques_counts.index[0] if len(enfoques_counts) > 0 else None
        }
    
    # Analizar etapas vitales
    if 'ETAPA VITAL \r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)' in df.columns:
        col_name = 'ETAPA VITAL \r\n(Según su apreciación, indique cual es el tipo de población que es su mayoría se atiende en el comedor)'
        etapas_data = df[col_name].dropna()
        
        all_etapas = []
        for entry in etapas_data:
            if pd.isna(entry) or entry == '':
                continue
            etapas = [e.strip() for e in str(entry).split(',')]
            all_etapas.extend(etapas)
        
        etapas_counts = pd.Series(all_etapas).value_counts()
        analysis['etapas_vitales'] = {
            'counts': etapas_counts,
            'total_menciones': len(all_etapas),
            'comedores_con_etapa': len(etapas_data),
            'mas_comun': etapas_counts.index[0] if len(etapas_counts) > 0 else None
        }
    
    return analysis

def analyze_needs_and_problems(df):
    """
    Analiza las necesidades y problemáticas identificadas
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        dict: Análisis de necesidades y problemáticas
    """
    if df is None or df.empty:
        return None
    
    analysis = {}
    
    # Analizar necesidades
    if 'NECESIDADES' in df.columns:
        necesidades_data = df['NECESIDADES'].dropna()
        
        all_necesidades = []
        for entry in necesidades_data:
            if pd.isna(entry) or entry == '':
                continue
            necesidades = [n.strip() for n in str(entry).split(',')]
            all_necesidades.extend(necesidades)
        
        necesidades_counts = pd.Series(all_necesidades).value_counts()
        analysis['necesidades'] = {
            'counts': necesidades_counts,
            'total_menciones': len(all_necesidades),
            'comedores_con_necesidades': len(necesidades_data),
            'mas_comun': necesidades_counts.index[0] if len(necesidades_counts) > 0 else None
        }
    
    # Analizar problemáticas
    if 'PROBLEMÁTICAS' in df.columns:
        problematicas_data = df['PROBLEMÁTICAS'].dropna()
        
        all_problematicas = []
        for entry in problematicas_data:
            if pd.isna(entry) or entry == '':
                continue
            problematicas = [p.strip() for p in str(entry).split(',')]
            all_problematicas.extend(problematicas)
        
        problematicas_counts = pd.Series(all_problematicas).value_counts()
        analysis['problematicas'] = {
            'counts': problematicas_counts,
            'total_menciones': len(all_problematicas),
            'comedores_con_problematicas': len(problematicas_data),
            'mas_comun': problematicas_counts.index[0] if len(problematicas_counts) > 0 else None
        }
    
    return analysis

def generate_summary_stats(df):
    """
    Genera estadísticas resumen del dataset
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        dict: Estadísticas resumen
    """
    if df is None or df.empty:
        return None
    
    stats = {
        'total_records': len(df),
        'total_columns': len(df.columns),
        'missing_data': df.isnull().sum().to_dict(),
        'data_types': df.dtypes.to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum(),
        'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
        'text_columns': df.select_dtypes(include=['object']).columns.tolist(),
        'unique_values': {col: df[col].nunique() for col in df.columns},
        'completeness': {col: (df[col].notna().sum() / len(df)) * 100 for col in df.columns}
    }
    
    return stats

def validate_data_quality(df):
    """
    Valida la calidad de los datos
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos de comedores
    
    Returns:
        dict: Reporte de calidad de datos
    """
    if df is None or df.empty:
        return None
    
    quality_report = {
        'total_records': len(df),
        'issues': [],
        'warnings': [],
        'recommendations': []
    }
    
    # Verificar columnas críticas
    critical_columns = [
        'TIPO DE COMEDOR',
        'NOMBRE DEL COMEDOR',
        'BARRIO',
        'COMUNA'
    ]
    
    for col in critical_columns:
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_percentage = (missing_count / len(df)) * 100
            
            if missing_percentage > 50:
                quality_report['issues'].append(
                    f"Columna crítica '{col}' tiene {missing_percentage:.1f}% de datos faltantes"
                )
            elif missing_percentage > 20:
                quality_report['warnings'].append(
                    f"Columna '{col}' tiene {missing_percentage:.1f}% de datos faltantes"
                )
        else:
            quality_report['issues'].append(f"Columna crítica '{col}' no encontrada")
    
    # Verificar duplicados por nombre de comedor
    if 'NOMBRE DEL COMEDOR' in df.columns:
        duplicates = df['NOMBRE DEL COMEDOR'].duplicated().sum()
        if duplicates > 0:
            quality_report['warnings'].append(
                f"Se encontraron {duplicates} nombres de comedores duplicados"
            )
    
    # Verificar consistencia en datos numéricos
    numeric_cols = ['COMUNA', 'NODO ', 'NICHO ', 'AÑO DE VINCULACIÓN AL PROGRAMA']
    for col in numeric_cols:
        if col in df.columns:
            # Intentar convertir a numérico y verificar errores
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            conversion_errors = numeric_series.isnull().sum() - df[col].isnull().sum()
            
            if conversion_errors > 0:
                quality_report['warnings'].append(
                    f"Columna '{col}': {conversion_errors} valores no pueden convertirse a número"
                )
    
    # Generar recomendaciones
    if len(quality_report['issues']) == 0 and len(quality_report['warnings']) == 0:
        quality_report['recommendations'].append("Los datos están en buen estado general")
    else:
        if len(quality_report['issues']) > 0:
            quality_report['recommendations'].append("Revisar y corregir los problemas críticos identificados")
        
        if len(quality_report['warnings']) > 0:
            quality_report['recommendations'].append("Considerar limpiar los datos según las advertencias")
    
    return quality_report

def filter_dataframe(df, filters):
    """
    Aplica filtros al DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame original
        filters (dict): Diccionario con filtros a aplicar
    
    Returns:
        pandas.DataFrame: DataFrame filtrado
    """
    if df is None or df.empty:
        return df
    
    df_filtered = df.copy()
    
    for column, value in filters.items():
        if column in df_filtered.columns and value and value != 'Todos' and value != 'Todas':
            if df_filtered[column].dtype == 'object':
                df_filtered = df_filtered[df_filtered[column] == value]
            else:
                df_filtered = df_filtered[df_filtered[column].astype(str) == str(value)]
    
    return df_filtered

def export_analysis_report(df, output_format='markdown'):
    """
    Exporta un reporte completo de análisis
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos
        output_format (str): Formato de salida ('markdown', 'html', 'json')
    
    Returns:
        str: Reporte formateado
    """
    if df is None or df.empty:
        return "No hay datos para generar el reporte"
    
    # Ejecutar todos los análisis
    tipo_analysis = analyze_tipo_comedor(df)
    geo_analysis = analyze_geographic_distribution(df)
    temporal_analysis = analyze_temporal_trends(df)
    population_analysis = analyze_population_focus(df)
    needs_analysis = analyze_needs_and_problems(df)
    summary_stats = generate_summary_stats(df)
    quality_report = validate_data_quality(df)
    
    if output_format == 'markdown':
        report = "# Reporte de Análisis de Comedores Comunitarios\n\n"
        
        # Resumen ejecutivo
        report += "## Resumen Ejecutivo\n\n"
        report += f"- **Total de comedores:** {len(df):,}\n"
        report += f"- **Columnas de datos:** {len(df.columns)}\n"
        
        if tipo_analysis[0] is not None:
            report += f"- **Tipos de comedores:** {len(tipo_analysis[0])}\n"
        
        if geo_analysis and 'comunas' in geo_analysis:
            report += f"- **Comunas cubiertas:** {geo_analysis['comunas']['total']}\n"
        
        # Análisis de tipos
        if tipo_analysis[1]:
            report += "\n" + tipo_analysis[1] + "\n"
        
        # Análisis geográfico
        if geo_analysis:
            report += "\n## Distribución Geográfica\n\n"
            for geo_type, data in geo_analysis.items():
                if 'mas_comedores' in data and data['mas_comedores']:
                    report += f"- **{geo_type.title()}:** {data['mas_comedores']} ({data['max_count']} comedores)\n"
        
        return report
    
    elif output_format == 'json':
        import json
        report_data = {
            'summary': summary_stats,
            'quality': quality_report,
            'tipo_analysis': {
                'counts': tipo_analysis[0].to_dict() if tipo_analysis[0] is not None else None,
                'analysis': tipo_analysis[1]
            },
            'geographic': geo_analysis,
            'temporal': temporal_analysis,
            'population': population_analysis,
            'needs': needs_analysis
        }
        return json.dumps(report_data, indent=2, default=str)
    
    else:
        return "Formato no soportado"