# 📊 Dashboard de KPIs — Online Retail

Dashboard interactivo desarrollado con **Streamlit** y **Plotly** para analizar los KPIs del dataset *Online Retail II*.

## 🚀 Cómo ejecutar el proyecto

### 1. Clonar el repositorio
```bash
git clone https://github.com/angelagiraldoing-coder/dashboard-retail-streamlit.git
cd dashboard-retail-streamlit
```
### 2. Descargar archivos data
Descargar los archivos de datos desde el siguiente enlace: 


Archivo csv original: online_retail_II.csv -> https://drive.google.com/file/d/1PmpGhoq0cEwTbS64GHL7rtXJv6Uqyiaz/view?usp=sharing

Archivo csv limpio: online_retail_II_clean.csv -> https://drive.google.com/file/d/1cthwq3BX3rDRFfI7nnD1ekV871cyQYGt/view?usp=sharing

### 3. Crear carpeta de procesamiento

Crear una carpeta llamada data en la raiz del proyecto y copiar los dos archivos csv descargados.

### 💡 Nota:
>Se recomienda utilizar el archivo csv limpio para el análisis, ya que contiene los datos limpios y preparados para el dashboard.
En caso de querer realizar la limpieza de datos, se puede utilizar el archivo csv original.

# Pasos para crear el ambiente virtual y ejecutar
### 1. Crear el venv
```bash
python3 -m venv venv
source venv/bin/activate
```
### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Preparar datos (OPCIONAL)
```bash
python process_data.py
```

### 4. Ejecutar Streamlit
```bash
streamlit run dashboard_kpis.py
```

### 💡 Nota 2:
> El comando `pip install -r requirements.txt` debe ejecutarse **con el `venv` activado** (verás `(venv)` al inicio de la línea en la terminal), de lo contrario las dependencias se instalarán de forma global en el sistema.
