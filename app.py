import streamlit as st
import pandas as pd
from fpdf import FPDF

# =============================================================================
# 1. CONFIGURACIÓN E INTERFAZ VISUAL (FRONTEND - ESTILO INDUSTRIAL OSCURO)
# =============================================================================
st.set_page_config(page_title="SLOTTING DINAMICO", layout="wide", initial_sidebar_state="collapsed")

# Inyección de CSS para forzar el modo oscuro industrial y acentos visuales
st.markdown("""
    <style>
    /* Fondo principal: Gris Pizarra Oscuro */
    .stApp {
        background-color: #0E1117;
        color: #E0E6ED;
    }
    /* Tipografía y color de Títulos: Naranja Seguridad Industrial */
    h1, h2, h3 {
        color: #FF9800 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    /* Estilización del File Uploader */
    div[data-testid="stFileUploader"] {
        background-color: #1A1C23;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px dashed #4B5563;
    }
    /* Cajas de Notificación (Success/Info) */
    div[data-testid="stAlert"] {
        background-color: #1A1C23;
        border-left: 5px solid #FF9800;
        color: #E0E6ED;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    /* Botón de Descarga A4 */
    .stDownloadButton > button {
        background-color: #FF9800;
        color: #000000;
        font-weight: 800;
        border: none;
        border-radius: 4px;
        width: 100%;
        padding: 15px;
        text-transform: uppercase;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        background-color: #E68A00;
        color: #FFFFFF;
        box-shadow: 0 0 10px rgba(255, 152, 0, 0.5);
    }
    /* Divisores */
    hr {
        border-top: 1px solid #4B5563;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏭 COMMAND CENTER: DYNAMIC SLOTTING")
st.markdown("### Sistema Inteligente de Soporte de Decisiones (DSS)")
st.write("Interfaz de ingeniería para la gestión algorítmica de layouts físicos y secuenciación de estiba de alta densidad.")
st.divider()

@st.cache_data
def cargar_bases_maestras():
    try:
        df_general = pd.read_excel("DATA GENERAL.xlsx")
        df_layout = pd.read_excel("ORDEN DE LAS TIENDAS.xlsx", dtype=str).fillna('')
        return df_general, df_layout
    except Exception as e:
        st.error(f"⚠️ Error de lectura de bases maestras locales: {e}.")
        return None, None

df_general, df_layout = cargar_bases_maestras()

@st.cache_data
def procesar_archivo_sap(file_buffer):
    dict_demanda = pd.read_excel(file_buffer, sheet_name=None)
    return pd.concat(dict_demanda.values(), ignore_index=True)

st.markdown("#### 📥 1. Ingesta de Demanda Transaccional (SAP)")
archivo_sap = st.file_uploader("Cargue el reporte multicapa diario (Formato .xlsx)", type=["xlsx"])

# =============================================================================
# 2. MOTOR LÓGICO: CONSOLIDACIÓN, LAYOUT Y WAVE PICKING
# =============================================================================
if archivo_sap is not None and df_general is not None and df_layout is not None:
    
    st.divider()
    
    with st.spinner("⚙️ Procesando matrices operativas y calculando tolerancias de estiba..."):
        
        df_demanda = procesar_archivo_sap(archivo_sap)
        
        # Limpieza de cabeceras
        df_demanda.columns = df_demanda.columns.str.strip()
        df_general.columns = df_general.columns.str.strip()
        
        # Detección de columnas clave
        col_mat_gen = df_general.columns[0]
        col_niv_gen = df_general.columns[1]
        col_mat_dem = df_demanda.columns[0]
        col_tienda = df_demanda.columns[1]
        col_cant = df_demanda.columns[4] 
        
        for col in df_general.columns:
            if 'esc' in str(col).lower() or 'mat' in str(col).lower(): col_mat_gen = col
            if 'evel' in str(col).lower() or 'ragil' in str(col).lower() or 'nivel' in str(col).lower(): col_niv_gen = col
        
        for col in df_demanda.columns:
            if 'esc' in str(col).lower() or 'mat' in str(col).lower(): col_mat_dem = col
            if 'store' in str(col).lower() or 'tiend' in str(col).lower() or 'centro' in str(col).lower(): col_tienda = col
            if 'cant' in str(col).lower(): col_cant = col

        df_gen_temp = df_general.rename(columns={col_mat_gen: 'Material Description', col_niv_gen: 'LEVEL'})
        df_dem_temp = df_demanda.rename(columns={col_mat_dem: 'Material Description'})

        # --- FASE 1: CÁLCULO DE ROTACIÓN Y LAYOUT DINÁMICO ---
        df_dem_temp['Tienda_Lista'] = df_dem_temp[col_tienda].astype(str).str.split(',')
        df_exploded = df_dem_temp.explode('Tienda_Lista')
        df_exploded['Tienda_Lista'] = df_exploded['Tienda_Lista'].str.strip()
        
        frecuencia_tiendas = df_exploded['Tienda_Lista'].value_counts().reset_index()
        frecuencia_tiendas.columns = ['Tienda', 'Volumen_Diario']
        tiendas_con_demanda = frecuencia_tiendas[frecuencia_tiendas['Tienda'].str.len() > 0]['Tienda'].tolist()

        tiendas_totales_layout = []
        for col_idx in range(len(df_layout.columns)):
            if 'TIENDA' in str(df_layout.columns[col_idx]).upper():
                for row_idx in range(len(df_layout)):
                    valor_celda = str(df_layout.iloc[row_idx, col_idx]).strip()
                    if valor_celda and valor_celda.upper() != 'NAN' and valor_celda != '':
                        if valor_celda not in tiendas_totales_layout:
                            tiendas_totales_layout.append(valor_celda)

        tiendas_sin_demanda = [t for t in tiendas_totales_layout if t not in tiendas_con_demanda]
        lista_maestra_ordenada = tiendas_con_demanda + tiendas_sin_demanda

        df_nuevo_layout = df_layout.copy().astype(str)
        idx_global = 0
        for col_idx in range(len(df_nuevo_layout.columns)):
            if 'TIENDA' in str(df_nuevo_layout.columns[col_idx]).upper():
                for row_idx in range(len(df_nuevo_layout)):
                    val_slot = str(df_nuevo_layout.iloc[row_idx, col_idx-1]).strip()
                    if val_slot != '' and val_slot.replace('.0', '').isdigit():
                        if idx_global < len(lista_maestra_ordenada):
                            df_nuevo_layout.iloc[row_idx, col_idx] = lista_maestra_ordenada[idx_global]
                            idx_global += 1

        # --- FASE 2: WAVE PICKING Y ESTIBA ESTRUCTURAL (5 NIVELES) ---
        df_dem_temp[col_cant] = pd.to_numeric(df_dem_temp[col_cant], errors='coerce').fillna(0)
        df_consolidado = df_dem_temp.groupby('Material Description', as_index=False)[col_cant].sum()
        df_consolidado.rename(columns={col_cant: 'Cantidad Total'}, inplace=True)
        
        df_picking = pd.merge(df_consolidado, df_gen_temp[['Material Description', 'LEVEL']], on="Material Description", how="left")
        
        def formato_operativo(t):
            t = str(t).lower()
            if '5' in t or 'ultra' in t: 
                return "Nivel 5 - Base Inf. (Ultra Resis.)", 5
            elif '4' in t or 'muy resis' in t: 
                return "Nivel 4 - Base Sup. (Muy Resis.)", 4
            elif '3' in t or 'normal' in t: 
                return "Nivel 3 - Centro Pallet (Normal)", 3
            elif '1' in t or 'muy frágil' in t or 'muy fragil' in t: 
                return "Nivel 1 - Cima Absoluta (Muy Frágil)", 1
            elif '2' in t or 'frágil' in t or 'fragil' in t: 
                return "Nivel 2 - Capa Sup. (Frágil)", 2
            else: 
                return "Nivel 3 - Centro Pallet (Por defecto)", 3

        resultados = df_picking['LEVEL'].fillna("3").apply(formato_operativo)
        df_picking['Posición en Pallet'] = [res[0] for res in resultados]
        df_picking['Prioridad_Orden'] = [res[1] for res in resultados]
        
        df_picking = df_picking.sort_values(by='Prioridad_Orden', ascending=False).reset_index(drop=True)
        df_vista_limpia = df_picking[['Material Description', 'Cantidad Total', 'Posición en Pallet']]

    st.success("✅ OPTIMIZACIÓN COMPLETADA: Matriz de 5 niveles aplicada exitosamente.")

    # Frontend de Resultados en Columnas
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🗺️ Mapeo Dinámico de Layout")
        st.dataframe(df_nuevo_layout, use_container_width=True, height=400)
    with col2:
        st.markdown("### 📦 Lista Consolidada de Estiba")
        st.dataframe(df_vista_limpia, use_container_width=True, height=400)

    st.divider()

    # =============================================================================
    # 3. MOTOR DE IMPRESIÓN A4 MIXTA (PDF)
    # =============================================================================
    class PDFReport(FPDF):
        def header(self):
            self.set_fill_color(30, 41, 59)
            self.set_text_color(255, 255, 255)
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'REPORTE OPERATIVO: SLOTTING & WAVE PICKING', 0, 1, 'C', True)
            self.ln(2)
            self.set_text_color(0, 0, 0)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Pagina {self.page_no()} - Documento de circulacion interna', 0, 0, 'C')

    def generar_pdf(layout_df, vista_limpia_df):
        pdf = PDFReport()
        
        # --- PÁGINA 1: LAYOUT ---
        pdf.add_page(orientation='L')
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 8, '1. MAPA DE REUBICACION COMPLETA DE SLOTS EN PLANTA', 0, 1, 'L')
        
        anchos = []
        for c in layout_df.columns:
            nombre = str(c).upper()
            if 'N°' in nombre: anchos.append(15)
            elif 'TIENDA' in nombre: anchos.append(35)
            else: anchos.append(8)
            
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        for i, col_name in enumerate(layout_df.columns):
            borde = 1 if anchos[i] > 10 else 0
            relleno = True if anchos[i] > 10 else False
            texto = str(col_name) if not 'UNNAMED' in str(col_name).upper() else ''
            pdf.cell(anchos[i], 6, texto.encode('latin-1', 'replace').decode('latin-1'), borde, 0, 'C', relleno)
        pdf.ln()
        
        pdf.set_font('Arial', '', 8)
        for index, row in layout_df.iterrows():
            for i, item in enumerate(row):
                borde = 1 if anchos[i] > 10 else 0
                val = str(item) if str(item) != 'nan' else ''
                pdf.cell(anchos[i], 5, val.encode('latin-1', 'replace').decode('latin-1'), borde, 0, 'C')
            pdf.ln()

        # --- PÁGINA 2: PICKING MAESTRO (5 NIVELES) ---
        pdf.add_page(orientation='P')
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(0, 10, '2. HOJA MAESTRA DE RECOLECCION Y ESTIBA ESTRUCTURAL (5 NIVELES)', 0, 1, 'L')
        
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(105, 7, 'Descripcion del Material', 1, 0, 'C', True)
        pdf.cell(20, 7, 'Cant.', 1, 0, 'C', True)
        pdf.cell(65, 7, 'Posicion de Apilamiento Seguro', 1, 1, 'C', True)
        
        pdf.set_font('Arial', '', 8)
        for _, fila in vista_limpia_df.iterrows():
            if pdf.get_y() > 270:
                pdf.add_page(orientation='P')
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(105, 7, 'Descripcion del Material', 1, 0, 'C', True)
                pdf.cell(20, 7, 'Cant.', 1, 0, 'C', True)
                pdf.cell(65, 7, 'Posicion de Apilamiento Seguro', 1, 1, 'C', True)
                pdf.set_font('Arial', '', 8)
                
            pdf.cell(105, 6, str(fila['Material Description'])[:55].encode('latin-1', 'replace').decode('latin-1'), 1, 0, 'L')
            cant_str = str(int(fila['Cantidad Total'])) if fila['Cantidad Total'] % 1 == 0 else str(fila['Cantidad Total'])
            pdf.cell(20, 6, cant_str, 1, 0, 'C')
            pdf.cell(65, 6, str(fila['Posición en Pallet']).encode('latin-1', 'replace').decode('latin-1'), 1, 1, 'C')
            
        return pdf.output(dest='S').encode('latin-1')

    pdf_bytes = generar_pdf(df_nuevo_layout, df_vista_limpia)
    
    st.markdown("#### 🖨️ 3. Generación de Hoja de Ruta Operativa")
    st.download_button(
        label="📄 DESCARGAR PDF CORPORATIVO (LISTO PARA IMPRESIÓN)",
        data=pdf_bytes,
        file_name="Plan_Slotting_Corporativo.pdf",
        mime="application/pdf"
    )