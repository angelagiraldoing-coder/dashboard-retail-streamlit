import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import os

st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Configuración de la página
st.set_page_config(
    page_title="Online Retail Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Dashboard de KPIs - Online Retail")
st.markdown("---")


# Cargar datos
@st.cache_data
def load_data():

    GDRIVE_FILE_ID = "1cthwq3BX3rDRFfI7nnD1ekV871cyQYGt"
    local_path = "data/online_retail_cleaned.csv"

    # Descargar solo si no existe localmente
    if not os.path.exists(local_path):
        os.makedirs("data", exist_ok=True)
        url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
        gdown.download(url, local_path, quiet=False)

    df = pd.read_csv(local_path, sep=";")

    # Se cambia para utilizar los datos online
    #df = pd.read_csv("data/online_retail_cleaned.csv", sep=";")

    # Convertir datos númericos
    df['TotalSales'] = pd.to_numeric(df['TotalSales'], errors='coerce')
    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')

    # Convertir fecha
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], format='%d/%m/%Y %H:%M')

    df = df.dropna(subset=['TotalSales', 'Quantity', 'InvoiceDate'])

    # Inclui esto para troubleshooting
    # print(df.info())

    return df


# Cargar datos
df = load_data()

# Filtrar solo ventas (sin devoluciones)
df_ventas = df[df['IsReturn'] == False].copy()

# ========================================
# SECCIÓN 1: KPIs PRINCIPALES (3 Tarjetas)
# ========================================

st.header("🎯 Métricas de Desempeño (KPIs)")

# Calcular KPIs
ingresos_totales = df_ventas['TotalSales'].sum()
cantidad_total_vendida = df_ventas['Quantity'].sum()
num_facturas = df_ventas['Invoice'].nunique()
ticket_promedio = ingresos_totales / num_facturas if num_facturas > 0 else 0

# Crear 3 columnas para las tarjetas
col1, col2, col3 = st.columns(3)

# KPI 1: Ingresos Totales
with col1:
    st.metric(
        label="💰 Ingresos Totales",
        value=f"${ingresos_totales:,.2f}",
        delta=f"{len(df_ventas):,} transacciones"
    )

# KPI 2: Cantidad Total Vendida
with col2:
    st.metric(
        label="📦 Cantidad Total de Productos Vendidos",
        value=f"{cantidad_total_vendida:,.0f}",
        delta=f"{df_ventas['StockCode'].nunique():,} productos únicos"
    )

# KPI 3: Ticket Promedio por Factura
with col3:
    st.metric(
        label="🧾 Ticket Promedio por Factura",
        value=f"${ticket_promedio:,.2f}",
        delta=f"{num_facturas:,} facturas"
    )

st.markdown("---")

# ========================================
# SECCIÓN 2: MÉTRICAS ADICIONALES
# ========================================

st.header("📈 Análisis Adicional")

col4, col5, col6, col7 = st.columns(4)

with col4:
    clientes_unicos = df_ventas[df_ventas['HasCustomerID'] == True]['CustomerID'].nunique()
    st.metric("👥 Clientes Únicos", f"{clientes_unicos:,}")

with col5:
    tasa_devolucion = (df['IsReturn'].sum() / len(df)) * 100
    st.metric("↩️ Tasa de Devolución", f"{tasa_devolucion:.2f}%")

with col6:
    paises = df_ventas['Country'].nunique()
    st.metric("🌍 Países", f"{paises}")

with col7:
    precio_promedio = df_ventas['UnitPrice'].mean()
    st.metric("💵 Precio Promedio", f"${precio_promedio:.2f}")

st.markdown("---")

# ========================================
# SECCIÓN 3: GRÁFICOS INTERACTIVOS
# ========================================

st.header("📊 Visualizaciones")

tab1, tab2, tab3 = st.tabs(["📅 Ventas por Tiempo", "🌎 Ventas por País", "🏆 Top Productos"])

# TAB 1: Ventas por Tiempo
with tab1:
    df_ventas['Fecha'] = df_ventas['InvoiceDate'].dt.date
    ventas_diarias = df_ventas.groupby('Fecha')['TotalSales'].sum().reset_index()

    fig_tiempo = px.line(
        ventas_diarias,
        x='Fecha',
        y='TotalSales',
        title='📈 Evolución de Ingresos Diarios',
        labels={'TotalSales': 'Ingresos ($)', 'Fecha': 'Fecha'}
    )
    fig_tiempo.update_traces(line_color='#1f77b4', line_width=2)
    st.plotly_chart(fig_tiempo, use_container_width=True)

# TAB 2: Ventas por País
with tab2:
    ventas_pais = df_ventas.groupby('Country')['TotalSales'].sum().sort_values(ascending=False).head(10).reset_index()

    fig_pais = px.bar(
        ventas_pais,
        x='TotalSales',
        y='Country',
        orientation='h',
        title='🌍 Top 10 Países por Ingresos',
        labels={'TotalSales': 'Ingresos ($)', 'Country': 'País'}
    )
    fig_pais.update_traces(marker_color='#2ca02c')
    st.plotly_chart(fig_pais, use_container_width=True)

# TAB 3: Top Productos
with tab3:
    top_productos = df_ventas.groupby('DescriptionCleaned').agg({
        'TotalSales': 'sum',
        'Quantity': 'sum'
    }).sort_values('TotalSales', ascending=False).head(15).reset_index()

    fig_productos = px.bar(
        top_productos,
        x='TotalSales',
        y='DescriptionCleaned',
        orientation='h',
        title='🏆 Top 15 Productos por Ingresos',
        labels={'TotalSales': 'Ingresos ($)', 'DescriptionCleaned': 'Producto'}
    )
    fig_productos.update_traces(marker_color='#ff7f0e')
    st.plotly_chart(fig_productos, use_container_width=True)

st.markdown("---")

# ========================================
# SECCIÓN 4: ANÁLISIS DE PRECIOS ATÍPICOS
# ========================================

st.header("🔎 Análisis de Precios Atípicos")

tab4, tab5 = st.tabs(["💰 Precios Atípicos", "🌍 Pareto de Ventas por País"])

# TAB 4: Análisis de precios atípicos
with tab4:
    st.subheader("Identificación de productos con precios inusuales")

    # Separar categorías de precios anómalos
    precios_cero = df_ventas[df_ventas['UnitPrice'] == 0].copy()

    # Calcular umbral de precios extremos usando percentil 80
    percentil_80 = df_ventas['UnitPrice'].quantile(0.80)
    precios_altos = df_ventas[df_ventas['UnitPrice'] > percentil_80].copy()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("🚫 Registros con precio = $0", f"{len(precios_cero):,}")
    with col_b:
        st.metric(f"📈 Registros con precio > ${percentil_80:.2f} (P80)", f"{len(precios_altos):,}")
    with col_c:
        st.metric("📊 Precio máximo registrado", f"${df_ventas['UnitPrice'].max():,.2f}")

    # Gráfico de dispersión: Cantidad vs Precio unitario
    st.markdown("#### Gráfico de Dispersión: Precio Unitario vs Cantidad")

    # Muestra representativa para el scatter (máx 5000 puntos para rendimiento)
    df_scatter = df_ventas.sample(min(5000, len(df_ventas)), random_state=42).copy()


    # Clasificar puntos
    def clasificar_precio(row):
        if row['UnitPrice'] == 0:
            return '🚫 Precio = $0'
        elif row['UnitPrice'] > percentil_80:
            return f'📈 Precio extremo (>${percentil_80:.0f})'
        else:
            return '✅ Normal'


    df_scatter['Clasificacion'] = df_scatter.apply(clasificar_precio, axis=1)

    color_map = {
        '✅ Normal': '#2ca02c',
        '🚫 Precio = $0': '#d62728',
        f'📈 Precio extremo (>${percentil_80:.0f})': '#ff7f0e'
    }

    fig_scatter = px.scatter(
        df_scatter,
        x='UnitPrice',
        y='Quantity',
        color='Clasificacion',
        color_discrete_map=color_map,
        hover_data=['DescriptionCleaned', 'Country', 'Invoice'],
        title='Dispersión de Precio Unitario vs Cantidad Vendida',
        labels={'UnitPrice': 'Precio Unitario ($)', 'Quantity': 'Cantidad', 'Clasificacion': 'Categoría'},
        opacity=0.6
    )
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Tablas detalladas
    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("#### 🚫 Productos con Precio = $0")
        st.caption("Posibles errores de sistema o muestras gratuitas")
        if len(precios_cero) > 0:
            tabla_cero = precios_cero.groupby('DescriptionCleaned').agg(
                Facturas_Mismo_Valor=('Invoice', 'count'),
                Cantidad_Total=('Quantity', 'sum'),
                Paises=('Country', 'nunique')
            ).sort_values('Facturas_Mismo_Valor', ascending=False).head(15).reset_index()
            tabla_cero.columns = ['Producto', '# Tx mismo valor', 'Cantidad Total', 'Países']
            st.dataframe(tabla_cero, use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron productos con precio $0.")

    with col_der:
        st.markdown(f"#### 📈 Productos con Precio Extremo (> P80: ${percentil_80:.2f})")
        st.caption("Posibles artículos premium, errores de captura o servicios especiales")
        if len(precios_altos) > 0:
            tabla_altos = precios_altos.groupby('DescriptionCleaned').agg(
                Precio_Max=('UnitPrice', 'max'),
                Precio_Promedio=('UnitPrice', 'mean'),
                Transacciones=('Invoice', 'count')
            ).sort_values('Precio_Max', ascending=False).head(15).reset_index()
            tabla_altos.columns = ['Producto', 'Precio Máx ($)', 'Precio Prom ($)', 'Transacciones']
            tabla_altos['Precio Máx ($)'] = tabla_altos['Precio Máx ($)'].round(2)
            tabla_altos['Precio Prom ($)'] = tabla_altos['Precio Prom ($)'].round(2)
            st.dataframe(tabla_altos, use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron precios extremos.")

    # Interpretación automática
    with st.expander("📝 Interpretación del Análisis"):
        st.markdown(f"""
        **Precios en $0 ({len(precios_cero):,} registros):**
        - Pueden representar **errores del sistema** al registrar transacciones sin precio, sin embargo
        también podrían ser **muestras gratuitas** o **ajustes contables** sin valor monetario.
        - Dado que ninguna de las transacciones fue única (siempre habian más transacciones con el mismo invoice) mi conclusión es que **son promociones o ajustes intencionales**.

        **Precios extremadamente altos (>{percentil_80:.2f} USD — percentil 80):**
        - Pueden corresponder a **artículos de alto valor** (muebles, sets completos, servicios premium).
        - El precio máximo registrado es **${df_ventas['UnitPrice'].max():,.2f}**, lo cual merece revisión manual.

        **Contexto del negocio:** Este es un retailer de artículos del hogar y regalos, 
        donde los precios normales oscilan entre **$0.10 y $20**. Valores superiores a 
        **${percentil_80:.0f}** son estadísticamente inusuales.
        """)

# TAB 5: Concentración de ventas (Pareto)
with tab5:
    st.subheader("Concentración de Ingresos por País — Principio de Pareto")

    # Calcular ventas por país (top N países)
    N_PAISES = 10
    ventas_por_pais = (
        df_ventas.groupby('Country')['TotalSales']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    ventas_por_pais.columns = ['País', 'Ingresos']

    total_ingresos = ventas_por_pais['Ingresos'].sum()
    top_n = ventas_por_pais.head(N_PAISES).copy()

    # Calcular porcentaje acumulado
    top_n['% del Total'] = (top_n['Ingresos'] / total_ingresos * 100).round(2)
    top_n['% Acumulado'] = top_n['% del Total'].cumsum().round(2)
    top_n['Ingresos (miles $)'] = (top_n['Ingresos'] / 1000).round(1)

    # Métricas resumen
    pct_top_n = top_n['% del Total'].sum()
    col1_p, col2_p, col3_p = st.columns(3)
    with col1_p:
        st.metric(f"🏆 % de ingresos generado por Top {N_PAISES} países", f"{pct_top_n:.1f}%")
    with col2_p:
        st.metric("🌍 Total de países en el dataset", f"{df_ventas['Country'].nunique()}")
    with col3_p:
        st.metric("💰 Ingresos totales (ventas)", f"${total_ingresos:,.0f}")

    # Gráfico de Pareto (barras + línea acumulada)
    fig_pareto = go.Figure()

    # Barras de ingresos
    fig_pareto.add_trace(go.Bar(
        name='Ingresos (miles $)',
        x=top_n['País'],
        y=top_n['Ingresos (miles $)'],
        marker_color='#1f77b4',
        yaxis='y',
        text=top_n['Ingresos (miles $)'].apply(lambda x: f"${x:.0f}K"),
        textposition='outside'
    ))

    # Línea de porcentaje acumulado
    fig_pareto.add_trace(go.Scatter(
        name='% Acumulado',
        x=top_n['País'],
        y=top_n['% Acumulado'],
        mode='lines+markers',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8, color='#d62728'),
        yaxis='y2',
        text=top_n['% Acumulado'].apply(lambda x: f"{x:.1f}%"),
        textposition='top center'
    ))

    # Línea de referencia al 80%
    fig_pareto.add_hline(
        y=80, yref='y2',
        line_dash='dash',
        line_color='orange',
        annotation_text='Umbral 80% (Regla de Pareto)',
        annotation_position='top right'
    )

    fig_pareto.update_layout(
        title=f'📊 Concentración de Ventas: Top {N_PAISES} Países (Gráfico de Pareto)',
        xaxis=dict(title='País', tickangle=-30),
        yaxis=dict(
            title='Ingresos (miles $)',
            tickfont=dict(color='#1f77b4')
        ),
        yaxis2=dict(
            title='% Acumulado de Ingresos',
            tickfont=dict(color='#d62728'),
            overlaying='y',
            side='right',
            range=[0, 110],
            ticksuffix='%'
        ),
        legend=dict(x=0.6, y=0.2),
        height=500,
        bargap=0.3
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    # Tabla detallada de los top N países
    st.markdown(f"#### 📋 Detalle: Top {N_PAISES} Países por Ingresos")
    tabla_paises = top_n[['País', 'Ingresos', '% del Total', '% Acumulado']].copy()
    tabla_paises['Ingresos'] = tabla_paises['Ingresos'].apply(lambda x: f"${x:,.2f}")
    tabla_paises['% del Total'] = tabla_paises['% del Total'].apply(lambda x: f"{x:.2f}%")
    tabla_paises['% Acumulado'] = tabla_paises['% Acumulado'].apply(lambda x: f"{x:.2f}%")
    st.dataframe(tabla_paises, use_container_width=True, hide_index=True)

    # Interpretación
    with st.expander("📝 Interpretación — Concentración de Ventas"):
        # Encontrar cuántos países representan el 80%
        paises_80 = top_n[top_n['% Acumulado'] <= 80.0]
        n_paises_80 = len(paises_80) + 1  # +1 para el que supera el 80%

        primer_pais = top_n.iloc[0]['País']
        pct_primer_pais = top_n.iloc[0]['% del Total']

        st.markdown(f"""
        **Hallazgos clave:**
        - Los **Top {N_PAISES} países** concentran el **{pct_top_n:.1f}%** del total de ingresos.
        - **{primer_pais}** domina ampliamente con el **{pct_primer_pais:.1f}%** de los ingresos totales.
        - **{n_paises_80} países** son suficientes para alcanzar el **80% de los ingresos** 
          (Principio de Pareto 80/20).
        - Los **{df_ventas['Country'].nunique() - N_PAISES} países restantes** 
          solo representan el **{100 - pct_top_n:.1f}%** de los ingresos.

        **Implicaciones para el negocio:**
        - Existe una **alta concentración geográfica** de ventas, lo que representa 
          tanto una fortaleza (mercados consolidados) como un riesgo (dependencia).
        - Se recomienda evaluar estrategias de **expansión en mercados secundarios** 
          con mayor potencial de crecimiento.
        - Los países con menor participación podrían beneficiarse de campañas 
          de marketing dirigidas o revisión de precios locales.
        """)

# ========================================
# SECCIÓN 6: TENDENCIA TEMPORAL MENSUAL
# ========================================

st.markdown("---")
st.header("📈 Tendencia Temporal de Ventas")

# Preparar datos mensuales
df_ventas['YearMonth'] = df_ventas['InvoiceDate'].dt.to_period('M').astype(str)
df_ventas['Year'] = df_ventas['InvoiceDate'].dt.year
df_ventas['Month'] = df_ventas['InvoiceDate'].dt.month
df_ventas['MonthName'] = df_ventas['InvoiceDate'].dt.strftime('%b')

ventas_mensuales = (
    df_ventas.groupby('YearMonth')
    .agg(
        Ingresos=('TotalSales', 'sum'),
        Transacciones=('Invoice', 'nunique')
    )
    .reset_index()
    .sort_values('YearMonth')
)

fig_tendencia = go.Figure()

# Línea de ingresos
fig_tendencia.add_trace(go.Scatter(
    x=ventas_mensuales['YearMonth'],
    y=ventas_mensuales['Ingresos'],
    mode='lines+markers',
    name='Ingresos ($)',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=7),
    hovertemplate='<b>%{x}</b><br>Ingresos: $%{y:,.0f}<extra></extra>'
))

# Resaltar mes de noviembre/diciembre (temporada navideña)
meses_navidenos = ventas_mensuales[
    ventas_mensuales['YearMonth'].str.contains('-11|-12', regex=True)
]
fig_tendencia.add_trace(go.Scatter(
    x=meses_navidenos['YearMonth'],
    y=meses_navidenos['Ingresos'],
    mode='markers',
    name='🎄 Temporada navideña',
    marker=dict(color='#d62728', size=14, symbol='star'),
    hovertemplate='<b>%{x}</b><br>Ingresos: $%{y:,.0f}<extra></extra>'
))

# Línea de tendencia (media móvil 3 meses)
if len(ventas_mensuales) >= 3:
    ventas_mensuales['MediaMovil'] = ventas_mensuales['Ingresos'].rolling(3, min_periods=1).mean()
    fig_tendencia.add_trace(go.Scatter(
        x=ventas_mensuales['YearMonth'],
        y=ventas_mensuales['MediaMovil'],
        mode='lines',
        name='Tendencia (media móvil 3m)',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        hovertemplate='<b>%{x}</b><br>Media móvil: $%{y:,.0f}<extra></extra>'
    ))

fig_tendencia.update_layout(
    title='📅 Evolución Mensual de Ingresos — Detección de Estacionalidad',
    xaxis_title='Mes',
    yaxis_title='Ingresos ($)',
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    hovermode='x unified',
    height=430
)
fig_tendencia.update_xaxes(tickangle=-45)

st.plotly_chart(fig_tendencia, use_container_width=True)

# Hallazgo automático de estacionalidad
mes_max = ventas_mensuales.loc[ventas_mensuales['Ingresos'].idxmax(), 'YearMonth']
mes_min = ventas_mensuales.loc[ventas_mensuales['Ingresos'].idxmin(), 'YearMonth']
ingreso_max = ventas_mensuales['Ingresos'].max()
ingreso_min = ventas_mensuales['Ingresos'].min()

col_s1, col_s2 = st.columns(2)
with col_s1:
    st.info(
        f"📈 **Mes con mayor ingreso:** {mes_max} — ${ingreso_max:,.0f}\n\nEsto confirma el **pico de temporada navideña** (Nov-Dic).")
with col_s2:
    st.warning(
        f"📉 **Mes con menor ingreso:** {mes_min} — ${ingreso_min:,.0f}\n\nLos meses de verano suelen mostrar **menor actividad** en este sector.")

# ========================================
# SECCIÓN 7: ANÁLISIS GEOGRÁFICO (MAPA)
# ========================================

st.markdown("---")
st.header("🗺️ Análisis Geográfico de Ventas")

# Obtener países únicos presentes en el dataset
paises_en_dataset = df_ventas['Country'].unique().tolist()

# Coordenadas completas de países (base de referencia)
coordenadas_paises_completo = {
    'United Kingdom': (55.3781, -3.4360),
    'Germany': (51.1657, 10.4515),
    'France': (46.2276, 2.2137),
    'Netherlands': (52.1326, 5.2913),
    'Spain': (40.4637, -3.7492),
    'Belgium': (50.5039, 4.4699),
    'Switzerland': (46.8182, 8.2275),
    'Portugal': (39.3999, -8.2245),
    'Australia': (-25.2744, 133.7751),
    'Norway': (60.4720, 8.4689),
    'Sweden': (60.1282, 18.6435),
    'Denmark': (56.2639, 9.5018),
    'Finland': (61.9241, 25.7482),
    'Austria': (47.5162, 14.5501),
    'Italy': (41.8719, 12.5674),
    'Japan': (36.2048, 138.2529),
    'Singapore': (1.3521, 103.8198),
    'United States': (37.0902, -95.7129),
    'Canada': (56.1304, -106.3468),
    'Brazil': (-14.2350, -51.9253),
    'EIRE': (53.1424, -7.6921),
    'Cyprus': (35.1264, 33.4299),
    'Greece': (39.0742, 21.8243),
    'Iceland': (64.9631, -19.0208),
    'Israel': (31.0461, 34.8516),
    'Lebanon': (33.8547, 35.8623),
    'Malta': (35.9375, 14.3754),
    'Poland': (51.9194, 19.1451),
    'Czech Republic': (49.8175, 15.4730),
    'Hungary': (47.1625, 19.5033),
    'Lithuania': (55.1694, 23.8813),
    'Latvia': (56.8796, 24.6032),
    'Estonia': (58.5953, 25.0136),
    'RSA': (-30.5595, 22.9375),
    'Bahrain': (26.0667, 50.5577),
    'United Arab Emirates': (23.4241, 53.8478),
    'Saudi Arabia': (23.8859, 45.0792),
    'Hong Kong': (22.3193, 114.1694),
}

# Filtrar coordenadas solo para países presentes en el dataset
coordenadas_paises = {
    pais: coords for pais, coords in coordenadas_paises_completo.items()
    if pais in paises_en_dataset
}

ventas_pais = (
    df_ventas.groupby('Country')['TotalSales']
    .sum()
    .reset_index()
    .rename(columns={'TotalSales': 'Ingresos'})
    .sort_values('Ingresos', ascending=False)
)

# Añadir coordenadas solo para países que tienen coordenadas definidas
ventas_pais['lat'] = ventas_pais['Country'].map(
    lambda c: coordenadas_paises.get(c, (None, None))[0]
)
ventas_pais['lon'] = ventas_pais['Country'].map(
    lambda c: coordenadas_paises.get(c, (None, None))[1]
)
ventas_pais = ventas_pais.dropna(subset=['lat', 'lon'])

# Tab para vista con y sin UK
tab_mapa1, tab_mapa2 = st.tabs(["🌍 Mapa Global (todos los países)", "🌍 Sin Reino Unido"])

with tab_mapa1:
    fig_mapa = px.scatter_geo(
        ventas_pais,
        lat='lat',
        lon='lon',
        size='Ingresos',
        color='Ingresos',
        hover_name='Country',
        hover_data={'Ingresos': ':,.0f', 'lat': False, 'lon': False},
        color_continuous_scale='Blues',
        size_max=60,
        title='💰 Ventas por País — Tamaño proporcional a ingresos',
        projection='natural earth'
    )
    fig_mapa.update_layout(height=450, coloraxis_colorbar_title='Ingresos ($)')
    st.plotly_chart(fig_mapa, use_container_width=True)

with tab_mapa2:
    ventas_sin_uk = ventas_pais[ventas_pais['Country'] != 'United Kingdom'].copy()

    # Top 3 mercados internacionales
    top3_internacional = ventas_sin_uk.head(3)

    fig_mapa2 = px.scatter_geo(
        ventas_sin_uk,
        lat='lat',
        lon='lon',
        size='Ingresos',
        color='Ingresos',
        hover_name='Country',
        hover_data={'Ingresos': ':,.0f', 'lat': False, 'lon': False},
        color_continuous_scale='Oranges',
        size_max=50,
        title='🌍 Mercados Internacionales (excl. Reino Unido)',
        projection='natural earth'
    )
    fig_mapa2.update_layout(height=450, coloraxis_colorbar_title='Ingresos ($)')
    st.plotly_chart(fig_mapa2, use_container_width=True)

    st.subheader("🏆 Top 3 Mercados Internacionales (excl. UK)")
    cols_top3 = st.columns(3)
    medallas = ['🥇', '🥈', '🥉']
    for i, (_, row) in enumerate(top3_internacional.iterrows()):
        with cols_top3[i]:
            pct_global = row['Ingresos'] / ventas_pais['Ingresos'].sum() * 100
            pct_intl = row['Ingresos'] / ventas_sin_uk['Ingresos'].sum() * 100
            st.metric(
                label=f"{medallas[i]} {row['Country']}",
                value=f"${row['Ingresos']:,.0f}",
                delta=f"{pct_intl:.1f}% del mercado internacional"
            )

    with st.expander("📝 Interpretación Geográfica"):
        top3_nombres = ', '.join(top3_internacional['Country'].tolist())
        st.markdown(f"""
        **Mercados internacionales clave:** {top3_nombres}
        
        - Excluyendo al Reino Unido (mercado principal), estos tres países concentran 
          la mayor parte de las ventas internacionales.
        - La concentración geográfica sugiere **oportunidades de expansión** en 
          mercados europeos o asiáticos con menor representación.
        - Se recomienda evaluar campañas de marketing localizadas para los mercados 
          con mayor potencial de crecimiento.
        """)

# ========================================
# SECCIÓN 8: COMPORTAMIENTO POR HORA
# ========================================

st.markdown("---")
st.header("⏰ Comportamiento de Compra por Hora del Día")

df_ventas['Hora'] = df_ventas['InvoiceDate'].dt.hour

ventas_hora = (
    df_ventas.groupby('Hora')
    .agg(
        Transacciones=('Invoice', 'nunique'),
        Ingresos=('TotalSales', 'sum'),
        Productos=('Quantity', 'sum')
    )
    .reset_index()
)


# Definir franjas horarias
def franja_horaria(h):
    if 6 <= h < 9:
        return '🌅 Madrugada (6-9h)'
    elif 9 <= h < 13:
        return '☀️ Mañana (9-13h)'
    elif 13 <= h < 17:
        return '🌤️ Tarde (13-17h)'
    elif 17 <= h < 21:
        return '🌆 Noche (17-21h)'
    else:
        return '🌙 Fuera de horario'


ventas_hora['Franja'] = ventas_hora['Hora'].apply(franja_horaria)

colores_hora = ventas_hora['Transacciones'].apply(
    lambda x: '#d62728' if x == ventas_hora['Transacciones'].max() else '#1f77b4'
)

fig_hora = go.Figure()
fig_hora.add_trace(go.Bar(
    x=ventas_hora['Hora'],
    y=ventas_hora['Transacciones'],
    name='Transacciones únicas',
    marker_color=colores_hora,
    hovertemplate='<b>%{x}:00h</b><br>Transacciones: %{y:,}<extra></extra>',
    text=ventas_hora['Transacciones'],
    textposition='outside'
))

# Línea de ingresos (eje secundario)
fig_hora.add_trace(go.Scatter(
    x=ventas_hora['Hora'],
    y=ventas_hora['Ingresos'],
    mode='lines+markers',
    name='Ingresos ($)',
    line=dict(color='#ff7f0e', width=2),
    marker=dict(size=6),
    yaxis='y2',
    hovertemplate='<b>%{x}:00h</b><br>Ingresos: $%{y:,.0f}<extra></extra>'
))

fig_hora.update_layout(
    title='📊 Volumen de Transacciones e Ingresos por Hora del Día',
    xaxis=dict(
        title='Hora del día',
        tickmode='array',
        tickvals=list(range(24)),
        ticktext=[f'{h}:00' for h in range(24)]
    ),
    yaxis=dict(title='Transacciones', tickfont=dict(color='#1f77b4')),
    yaxis2=dict(
        title='Ingresos ($)',
        tickfont=dict(color='#ff7f0e'),
        overlaying='y',
        side='right',
        tickformat='$,.0f'
    ),
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    height=430,
    bargap=0.1
)

st.plotly_chart(fig_hora, use_container_width=True)

# Franjas horarias consolidadas
st.subheader("📊 Resumen por Franja Horaria")
ventas_franja = (
    ventas_hora.groupby('Franja')
    .agg(
        Transacciones=('Transacciones', 'sum'),
        Ingresos=('Ingresos', 'sum')
    )
    .reset_index()
    .sort_values('Transacciones', ascending=False)
)

hora_pico = ventas_hora.loc[ventas_hora['Transacciones'].idxmax(), 'Hora']
franja_pico = ventas_hora.loc[ventas_hora['Transacciones'].idxmax(), 'Franja']
transacciones_pico = ventas_hora['Transacciones'].max()

col_h1, col_h2, col_h3 = st.columns(3)
with col_h1:
    st.metric("🔥 Hora Pico", f"{hora_pico}:00h", f"{transacciones_pico:,} transacciones")
with col_h2:
    st.metric("🕐 Franja Más Activa", franja_pico.split('(')[0].strip())
with col_h3:
    horas_inactivas = ventas_hora[ventas_hora['Transacciones'] == 0]['Hora'].count()
    st.metric("🌙 Horas sin actividad", f"{horas_inactivas}", "horas del día")

with st.expander("📝 Implicaciones para Soporte al Cliente"):
    st.markdown(f"""
    **Hallazgos clave:**
    - El **pico máximo de transacciones** ocurre a las **{hora_pico}:00h**, 
      lo que indica que la mayoría de los pedidos se procesan en horario de oficina.
    - La franja **{franja_pico}** concentra el mayor volumen de actividad comercial.
    
    **Recomendaciones para soporte:**
    - 📞 **Asignar más agentes** entre las **9:00 y 14:00h** para atender consultas en tiempo real.
    - 🤖 **Implementar chatbot/autoservicio** para consultas fuera de horario pico.
    - 📧 **Responder correos nocturnos** a primera hora del día siguiente.
    - 🔔 **Alertas de sistema** configuradas para las horas de mayor carga transaccional.
    """)

# ========================================
# SECCIÓN 9: SEGMENTACIÓN DINÁMICA (SLICER)
# ========================================

st.markdown("---")
st.header("🎛️ Segmentación Dinámica por País y Período")

st.markdown("""
Utiliza los filtros para explorar el comportamiento de ventas en mercados específicos 
y comparar el **ticket promedio** con el promedio global.
""")

# Filtros en columnas
col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 1])

paises_disponibles = sorted(df_ventas['Country'].unique().tolist())

with col_filtro1:
    pais_seleccionado = st.selectbox(
        "🌍 Seleccionar País",
        options=paises_disponibles,
        index=paises_disponibles.index('Australia') if 'Australia' in paises_disponibles else 0,
        key='slicer_pais'
    )

with col_filtro2:
    periodos_disponibles = sorted(df_ventas['YearMonth'].unique().tolist())
    periodo_seleccionado = st.select_slider(
        "📅 Rango de Período",
        options=periodos_disponibles,
        value=(periodos_disponibles[0], periodos_disponibles[-1]),
        key='slicer_periodo'
    )

with col_filtro3:
    st.markdown("<br>", unsafe_allow_html=True)
    solo_productos = st.checkbox("Solo productos", value=True, key='slicer_productos')

# Filtrar datos según selección
mask_periodo = (
        (df_ventas['YearMonth'] >= periodo_seleccionado[0]) &
        (df_ventas['YearMonth'] <= periodo_seleccionado[1])
)

if solo_productos:
    df_base = df_ventas[mask_periodo & (df_ventas['UnitPrice'] > 0)].copy()
else:
    df_base = df_ventas[mask_periodo].copy()

df_filtrado = df_base[df_base['Country'] == pais_seleccionado].copy()

# Calcular métricas comparativas
if len(df_filtrado) > 0:
    # Ticket promedio global (período seleccionado)
    facturas_global = df_base.groupby('Invoice')['TotalSales'].sum()
    ticket_global = facturas_global.mean() if len(facturas_global) > 0 else 0

    # Ticket promedio del país seleccionado
    facturas_pais = df_filtrado.groupby('Invoice')['TotalSales'].sum()
    ticket_pais = facturas_pais.mean() if len(facturas_pais) > 0 else 0

    diferencia_pct = ((ticket_pais - ticket_global) / ticket_global * 100) if ticket_global > 0 else 0

    # Métricas del país
    ingresos_pais = df_filtrado['TotalSales'].sum()
    num_facturas_pais = df_filtrado['Invoice'].nunique()
    productos_pais = df_filtrado['Quantity'].sum()

    # KPIs del país vs global
    st.subheader(f"📊 Análisis: {pais_seleccionado} | {periodo_seleccionado[0]} → {periodo_seleccionado[1]}")

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.metric(
            "💰 Ingresos totales",
            f"${ingresos_pais:,.0f}"
        )
    with col_k2:
        st.metric(
            "🧾 Ticket Promedio País",
            f"${ticket_pais:,.2f}",
            delta=f"{diferencia_pct:+.1f}% vs global",
            delta_color="normal"
        )
    with col_k3:
        st.metric(
            "🌐 Ticket Promedio Global",
            f"${ticket_global:,.2f}",
            delta=f"Período seleccionado"
        )
    with col_k4:
        st.metric(
            "📦 Facturas",
            f"{num_facturas_pais:,}"
        )

    # Gráfico de evolución del ticket por mes para el país vs global
    ticket_mensual_pais = (
        df_filtrado.groupby(['YearMonth', 'Invoice'])['TotalSales']
        .sum()
        .reset_index()
        .groupby('YearMonth')['TotalSales']
        .mean()
        .reset_index()
        .rename(columns={'TotalSales': 'Ticket_Pais'})
    )

    ticket_mensual_global = (
        df_base.groupby(['YearMonth', 'Invoice'])['TotalSales']
        .sum()
        .reset_index()
        .groupby('YearMonth')['TotalSales']
        .mean()
        .reset_index()
        .rename(columns={'TotalSales': 'Ticket_Global'})
    )

    ticket_comparado = ticket_mensual_pais.merge(ticket_mensual_global, on='YearMonth', how='outer').sort_values(
        'YearMonth')

    fig_ticket = go.Figure()
    fig_ticket.add_trace(go.Scatter(
        x=ticket_comparado['YearMonth'],
        y=ticket_comparado['Ticket_Pais'],
        mode='lines+markers',
        name=f'Ticket {pais_seleccionado}',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Ticket ' + pais_seleccionado + ': $%{y:,.2f}<extra></extra>'
    ))
    fig_ticket.add_trace(go.Scatter(
        x=ticket_comparado['YearMonth'],
        y=ticket_comparado['Ticket_Global'],
        mode='lines+markers',
        name='Ticket Promedio Global',
        line=dict(color='#1f77b4', width=2, dash='dash'),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Ticket Global: $%{y:,.2f}<extra></extra>'
    ))

    fig_ticket.update_layout(
        title=f'📈 Comparación de Ticket Promedio: {pais_seleccionado} vs Promedio Global',
        xaxis_title='Período',
        yaxis_title='Ticket Promedio ($)',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        height=380,
        hovermode='x unified'
    )
    fig_ticket.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_ticket, use_container_width=True)

    # Top productos del país seleccionado
    col_prod, col_interp = st.columns([3, 2])
    with col_prod:
        st.subheader(f"🏆 Top 5 Productos en {pais_seleccionado}")
        top_productos_pais = (
            df_filtrado.groupby('DescriptionCleaned')
            .agg(Ingresos=('TotalSales', 'sum'), Cantidad=('Quantity', 'sum'))
            .sort_values('Ingresos', ascending=False)
            .head(5)
            .reset_index()
        )
        top_productos_pais['Ingresos'] = top_productos_pais['Ingresos'].apply(lambda x: f"${x:,.2f}")
        top_productos_pais.columns = ['Producto', 'Ingresos', 'Cantidad Vendida']
        st.dataframe(top_productos_pais, use_container_width=True, hide_index=True)

    with col_interp:
        st.subheader("💡 Interpretación")
        if diferencia_pct > 10:
            st.success(f"""
            **{pais_seleccionado}** tiene un ticket promedio **{diferencia_pct:.1f}% MAYOR** 
            al global (${ticket_pais:,.2f} vs ${ticket_global:,.2f}).
            
            Esto sugiere que los clientes de este mercado realizan **compras de mayor valor** 
            o adquieren más productos por pedido.
            """)
        elif diferencia_pct < -10:
            st.warning(f"""
            **{pais_seleccionado}** tiene un ticket promedio **{abs(diferencia_pct):.1f}% MENOR** 
            al global (${ticket_pais:,.2f} vs ${ticket_global:,.2f}).
            
            Posibles causas: compras más pequeñas, diferente mix de productos, 
            o mercado en etapa de desarrollo.
            """)
        else:
            st.info(f"""
            **{pais_seleccionado}** tiene un ticket promedio **similar** al global 
            (${ticket_pais:,.2f} vs ${ticket_global:,.2f}).
            
            Diferencia de solo {diferencia_pct:+.1f}%, indicando comportamiento 
            de compra **alineado con la media**.
            """)
else:
    st.warning(f"⚠️ No hay datos disponibles para **{pais_seleccionado}** en el período seleccionado.")

st.markdown("---")
st.header("Datos crudos")
# ========================================
# TABLA DE DATOS
# ========================================

with st.expander("📋 Ver Datos Crudos"):
    st.dataframe(
        df_ventas[
            ['Invoice', 'DescriptionCleaned', 'Quantity', 'UnitPrice', 'TotalSales', 'Country', 'InvoiceDate']].head(
            100),
        use_container_width=True
    )

# Pie de página
st.markdown("---")
st.caption("Dashboard creado con Streamlit | Dataset: Online Retail II | Angela Marcela Giraldo Reyes")
