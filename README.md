# 🏭 DSS: Dynamic Slotting & Wave Picking Optimizer

Sistema de Soporte de Decisiones diseñado en Python para optimizar la rentabilidad de centros de distribución de alta densidad.

## 🚀 Impacto Operativo y Financiero
* **Reubicación Dinámica (Layout):** Algoritmo que clasifica la demanda diaria (ABC) y asigna las tiendas de mayor rotación a las zonas de despacho inmediato, contrayendo el **Tiempo Estándar (TE)** de los recorridos.
* **Consolidación Wave Picking:** Centraliza el volumen de pedidos diarios para reducir el número de visitas a un mismo pasillo, minimizando horas-hombre.
* **Estiba Estructural (5 Niveles):** Mapeo automatizado de fragilidad para asegurar que la base pesada soporte el pallet, eliminando el costo oculto por mermas o aplastamiento.

## 🛠️ Tecnologías Aplicadas
* **Python (Pandas):** Procesamiento de matrices complejas y consolidación multicapa (ETL).
* **Streamlit:** Interfaz gráfica industrial (Frontend).
* **FPDF:** Generación automática de Hojas de Ruta Operativa Estándar (SOE) en formato A4 Mixto.

*Nota: Por políticas de confidencialidad y gobernanza de datos, los archivos transaccionales reales (.xlsx) se encuentran excluidos de este repositorio público.*
