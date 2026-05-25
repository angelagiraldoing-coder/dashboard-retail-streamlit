from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, trim, upper, regexp_replace, count, sum as spark_sum, isnan
from pyspark.sql.types import DoubleType
import os
import shutil

# Inicializar Spark Session
spark = SparkSession.builder \
    .appName("RetailDataCleaning") \
    .master("local[*]") \
    .config("spark.driver.memory", "8g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

# Rutas
input_path = "data/online_retail_II.csv"
output_dir = "data/"

# 1. CARGA DE DATOS
print("=" * 80)
print("CARGANDO DATOS...")
print("=" * 80)

df_raw = spark.read.csv(
    input_path,
    header=True,
    inferSchema=True,
    sep=";",
    encoding="UTF-8"
)

# Mostrar esquema inicial
print("\nESQUEMA DEL DATASET:")
df_raw.printSchema()

# Contar registros totales
total_records = df_raw.count()
print(f"\nTotal de registros: {total_records:,}")

# Mostrar muestra
print("\nMUESTRA DE DATOS:")
df_raw.show(5, truncate=False)

# 2. ANÁLISIS INICIAL DE CALIDAD DE DATOS
print("\n" + "=" * 80)
print("ANÁLISIS DE CALIDAD DE DATOS")
print("=" * 80)

# Valores nulos por columna
print("\nVALORES NULOS POR COLUMNA:")
df_raw.select([count(when(col(c).isNull(), c)).alias(c) for c in df_raw.columns]).show(vertical=True)

# Estadísticas descriptivas
print("\nESTADÍSTICAS DESCRIPTIVAS:")
df_raw.describe().show()


# =============================================================================
# LIMPIEZA 1: TRATAMIENTO DE DEVOLUCIONES
# =============================================================================
print("\n" + "=" * 80)
print("PREGUNTA 1: ANÁLISIS DE DEVOLUCIONES")
print("=" * 80)

# Identificar transacciones con cantidades negativas
df_with_returns_flag = df_raw.withColumn(
    "IsReturn",
    when(col("Quantity") < 0, True).otherwise(False)
)

# Identificar facturas que empiezan con 'C' (cancelaciones)
df_with_returns_flag = df_with_returns_flag.withColumn(
    "IsCancellation",
    when(col("Invoice").startswith("C"), True).otherwise(False)
)

# Estadísticas de devoluciones
total_transactions = df_with_returns_flag.count()
returns_by_quantity = df_with_returns_flag.filter(col("IsReturn") == True).count()
returns_by_invoice = df_with_returns_flag.filter(col("IsCancellation") == True).count()

print(f"\nTotal de transacciones: {total_transactions:,}")
print(f"Transacciones con cantidad negativa: {returns_by_quantity:,} ({returns_by_quantity/total_transactions*100:.2f}%)")
print(f"Facturas con código 'C': {returns_by_invoice:,} ({returns_by_invoice/total_transactions*100:.2f}%)")

# Calcular impacto en ingresos (necesitamos limpiar Price primero)
df_price_cleaned = df_with_returns_flag.withColumn(
    "PriceNumeric",
    regexp_replace(col("Price"), ",", ".").cast(DoubleType())
)

df_price_cleaned = df_price_cleaned.withColumn(
    "TotalSales",
    col("Quantity") * col("PriceNumeric")
)

# Ingresos con y sin devoluciones
total_revenue_with_returns = df_price_cleaned.agg(spark_sum("TotalSales")).collect()[0][0]
total_revenue_without_returns = df_price_cleaned.filter(col("Quantity") > 0).agg(spark_sum("TotalSales")).collect()[0][0]

print(f"\nIngresos totales (con devoluciones): ${total_revenue_with_returns:,.2f}")
print(f"Ingresos totales (sin devoluciones): ${total_revenue_without_returns:,.2f}")
print(f"Impacto de devoluciones: ${total_revenue_with_returns - total_revenue_without_returns:,.2f}")


# =============================================================================
# LIMPIEZA 2: DEPURACIÓN DE CLIENTES
# =============================================================================
print("\n" + "=" * 80)
print("PREGUNTA 2: ANÁLISIS DE CLIENTES ANÓNIMOS")
print("=" * 80)

# Identificar registros sin CustomerID
df_customer_analysis = df_price_cleaned.withColumn(
    "HasCustomerID",
    when(col("Customer ID").isNull(), False).otherwise(True)
)

# Contar registros sin CustomerID
total_with_customer = df_customer_analysis.filter(col("HasCustomerID") == True).count()
total_without_customer = df_customer_analysis.filter(col("HasCustomerID") == False).count()

print(f"\nTransacciones con CustomerID: {total_with_customer:,} ({total_with_customer/total_transactions*100:.2f}%)")
print(f"Transacciones sin CustomerID: {total_without_customer:,} ({total_without_customer/total_transactions*100:.2f}%)")

# Calcular ventas de clientes anónimos (solo ventas positivas)
sales_with_customer = df_customer_analysis.filter(
    (col("HasCustomerID") == True) & (col("Quantity") > 0)
).agg(spark_sum("TotalSales")).collect()[0][0]

sales_without_customer = df_customer_analysis.filter(
    (col("HasCustomerID") == False) & (col("Quantity") > 0)
).agg(spark_sum("TotalSales")).collect()[0][0]

total_sales_positive = sales_with_customer + sales_without_customer

print(f"\nVentas con CustomerID: ${sales_with_customer:,.2f} ({sales_with_customer/total_sales_positive*100:.2f}%)")
print(f"Ventas sin CustomerID (anónimos): ${sales_without_customer:,.2f} ({sales_without_customer/total_sales_positive*100:.2f}%)")

print("\nESTRATEGIA RECOMENDADA:")
print("   1. Mantener registros anónimos en tabla separada para análisis de ventas globales")
print("   2. Excluir anónimos del análisis de lealtad/comportamiento de clientes")
print("   3. Crear segmento 'Guest Customers' en Power BI con filtros específicos")


# =============================================================================
# LIMPIEZA 3: ESTANDARIZACIÓN DE CATÁLOGO
# =============================================================================
print("\n" + "=" * 80)
print("PREGUNTA 3: ESTANDARIZACIÓN DE DESCRIPCIONES")
print("=" * 80)

# Mostrar problemas comunes
print("\nMUESTRA DE DESCRIPCIONES CON PROBLEMAS:")
df_customer_analysis.select("Description").filter(
    col("Description").isNull() |
    (col("Description") == "") |
    col("Description").contains("POSTAGE") |
    col("Description").contains("BANK CHARGES")
).distinct().show(20, truncate=False)

# Aplicar transformaciones de limpieza
df_cleaned = df_customer_analysis.withColumn(
    "DescriptionCleaned",
    # Paso 1: Eliminar espacios extras
    trim(col("Description"))
)

df_cleaned = df_cleaned.withColumn(
    "DescriptionCleaned",
    # Paso 2: Convertir a mayúsculas consistente (ya están, pero por si acaso)
    upper(col("DescriptionCleaned"))
)

df_cleaned = df_cleaned.withColumn(
    "DescriptionCleaned",
    # Paso 3: Reemplazar nulos con "UNKNOWN"
    when(col("DescriptionCleaned").isNull(), "UNKNOWN").otherwise(col("DescriptionCleaned"))
)

# Categorizar productos especiales (servicios, no productos)
df_cleaned = df_cleaned.withColumn(
    "ProductCategory",
    when(col("DescriptionCleaned").contains("POSTAGE"), "SERVICE_SHIPPING")
    .when(col("DescriptionCleaned").contains("BANK CHARGES"), "SERVICE_FEES")
    .when(col("DescriptionCleaned").contains("DISCOUNT"), "SERVICE_DISCOUNT")
    .when(col("DescriptionCleaned").contains("CARRIAGE"), "SERVICE_SHIPPING")
    .when(col("DescriptionCleaned") == "UNKNOWN", "UNKNOWN")
    .otherwise("PRODUCT")
)

# Contar por categoría
print("\nDISTRIBUCIÓN POR TIPO DE PRODUCTO:")
df_cleaned.groupBy("ProductCategory").count().orderBy(col("count").desc()).show()

print("\nTRANSFORMACIONES APLICADAS:")
print("   1. Espacios en blanco eliminados (trim)")
print("   2. Texto normalizado a mayúsculas")
print("   3. Valores nulos reemplazados por 'UNKNOWN'")
print("   4. Categorización de servicios vs productos")


# =============================================================================
# EXPORTACIÓN DE DATOS LIMPIOS
# =============================================================================
print("\n" + "=" * 80)
print("EXPORTANDO DATOS PROCESADOS")
print("=" * 80)

# Seleccionar columnas finales
df_final = df_cleaned.select(
    col("Invoice"),
    col("StockCode"),
    col("Description"),
    col("DescriptionCleaned"),
    col("ProductCategory"),
    col("Quantity"),
    col("InvoiceDate"),
    col("PriceNumeric").alias("UnitPrice"),
    col("Customer ID").alias("CustomerID"),
    col("Country"),
    col("TotalSales"),
    col("IsReturn"),
    col("IsCancellation"),
    col("HasCustomerID")
)

# Guardar en Parquet (eficiente)
print("\nGuardando en formato Parquet...")
df_final.write.mode("overwrite").parquet(f"{output_dir}online_retail_cleaned.parquet")

# Guardar en CSV (para Power BI) - con nombre limpio
print("Guardando en formato CSV...")
temp_csv_dir = f"{output_dir}temp_csv_output"

# Escribir a directorio temporal
df_final.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .option("sep", ";") \
    .csv(temp_csv_dir)

# Encontrar el archivo part-*.csv y renombrarlo
csv_filename = "online_retail_cleaned.csv"
csv_output_path = f"{output_dir}{csv_filename}"

# Buscar el archivo part-*.csv en el directorio temporal
for filename in os.listdir(temp_csv_dir):
    if filename.startswith("part-") and filename.endswith(".csv"):
        # Copiar y renombrar el archivo
        shutil.move(
            os.path.join(temp_csv_dir, filename),
            csv_output_path
        )
        print(f"CSV renombrado a: {csv_filename}")
        break

# Eliminar directorio temporal con archivos .crc y _SUCCESS
shutil.rmtree(temp_csv_dir)
print("Archivos temporales eliminados")

print("\nPROCESAMIENTO COMPLETADO EXITOSAMENTE!")
print(f"Archivos generados:")
print(f"   - Parquet: {output_dir}online_retail_cleaned.parquet/")
print(f"   - CSV:     {output_dir}{csv_filename}")

# Cerrar Spark
spark.stop()