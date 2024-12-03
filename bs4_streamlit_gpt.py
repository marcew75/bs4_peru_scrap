import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time


st.title("¡Despliegue Exitoso!")
st.write("Si ves esto, Streamlit está funcionando correctamente.")




# Función para hacer clic en el botón de "Mostrar más" con Selenium
def preparar_sitio_web(marca, categoria):
    options = Options()
    options.add_argument("--headless")  # Modo sin cabeza para Selenium
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    try:
        url = f"https://pe.wiautomation.com/busqueda?marca={marca}&categoria={categoria}"  # Cambia según tu caso
        driver.get(url)

        # Intentar hacer clic en el botón de "Mostrar más"
        try:
            boton_mostrar_mas = driver.find_element(By.CSS_SELECTOR, "button.mostrar-mas")  # Ajusta el selector al botón
            boton_mostrar_mas.click()
            time.sleep(3)  # Espera a que cargue el contenido
        except Exception as e:
            st.warning("No se encontró o no se pudo hacer clic en el botón de 'Mostrar más'. Continuando...")

        # Recuperar el HTML actualizado
        html_actualizado = driver.page_source
    finally:
        driver.quit()

    return html_actualizado

# Función para realizar scraping con paginación clásica
def realizar_scraping(marca, categoria):
    productos = []
    base_url = f"https://pe.wiautomation.com/busqueda?marca={marca}&categoria={categoria}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    }

    # Paso 1: Preparar la página con Selenium
    html = preparar_sitio_web(marca, categoria)
    soup = BeautifulSoup(html, "html.parser")

    # Paso 2: Extraer datos de la página inicial
    for contenedor in soup.select("div.item_content"):
        try:
            descripcion = contenedor.select_one("span.name").text.strip()
            imagen_url = contenedor.select_one("img").get("src")
            precio = contenedor.select_one("div.price").text.strip()
            productos.append({
                "Descripción": descripcion,
                "URL Imagen": imagen_url,
                "Precio": precio
            })
        except Exception:
            continue

    # Paso 3: Navegar por la paginación (hasta 5 páginas)
    for page in range(2, 6):  # Páginas 2 a 5
        url = f"{base_url}&page={page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            st.warning(f"No se pudo acceder a la página {page}.")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        for contenedor in soup.select("div.item_content"):
            try:
                descripcion = contenedor.select_one("span.name").text.strip()
                imagen_url = contenedor.select_one("img").get("src")
                precio = contenedor.select_one("div.price").text.strip()
                productos.append({
                    "Descripción": descripcion,
                    "URL Imagen": imagen_url,
                    "Precio": precio
                })
            except Exception:
                continue

    return pd.DataFrame(productos)

# Función para convertir a Excel
def convertir_a_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    return output.getvalue()

# Interfaz de usuario
st.title("Scraper de Productos (Requests + Selenium)")
marca = st.text_input("Marca", value="ABB")
categoria = st.text_input("Categoría", value="Fuente-de-alimentación")

if st.button("Realizar Búsqueda"):
    with st.spinner("Realizando búsqueda..."):
        df = realizar_scraping(marca, categoria)

    if not df.empty:
        st.success("Búsqueda completada con éxito.")
        st.dataframe(df)

        archivo_excel = convertir_a_excel(df)
        st.download_button(
            label="Descargar Resultados en Excel",
            data=archivo_excel,
            file_name=f"resultados_{marca}_{categoria}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No se encontraron productos.")
