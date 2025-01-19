import requests
from bs4 import BeautifulSoup
from download_pubmed import buscar_articulos, obtener_detalles_articulo
from urllib.parse import urljoin

def es_pdf_valido(response):
    """Verifica si la respuesta contiene un archivo PDF válido"""
    content_type = response.headers.get("Content-Type", "")
    return "application/pdf" in content_type

def obtener_enlace_real_pdf(full_text_link):
    """Extrae el enlace real al PDF desde la web del artículo"""
    try:
        response = requests.get(full_text_link, timeout=10)
        if response.status_code != 200:
            print(f"❌ No se pudo acceder a {full_text_link}. Código: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Buscar enlaces que contengan 'pdf' en la URL
        posibles_links = [a["href"] for a in soup.find_all("a", href=True) if "pdf" in a["href"].lower()]
        
        if posibles_links:
            pdf_link = posibles_links[0]
            
            # Si el enlace es relativo, convertirlo en absoluto usando urljoin
            if not pdf_link.startswith("http"):
                pdf_link = urljoin(full_text_link, pdf_link)

            print(f"✅ Enlace real al PDF encontrado: {pdf_link}")
            return pdf_link
        
        print("⚠ No se encontró un enlace directo al PDF en la página.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al acceder a la página del artículo: {e}")
        return None

def descargar_desde_web_oficial(full_text_link, doi):
    """Descarga el artículo desde la web oficial, buscando el enlace real al PDF"""
    pdf_url = obtener_enlace_real_pdf(full_text_link)
    
    if not pdf_url:
        print(f"⚠ No se pudo encontrar el PDF en la web oficial de {full_text_link}")
        return False

    try:
        response = requests.get(pdf_url, timeout=10, stream=True)
        if response.status_code != 200:
            print(f"❌ No se pudo descargar el PDF desde {pdf_url}. Código: {response.status_code}")
            return False
        
        filename = f"{doi.replace('/', '_')}.pdf"
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        
        print(f"✅ Artículo guardado correctamente desde la web oficial: {filename}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Error al intentar descargar el PDF: {e}")
        return False

def descargar_desde_scihub(doi):
    """Descarga un artículo desde Sci-Hub usando su DOI"""
    if doi == "No DOI available":
        print("⚠ No se encontró un DOI para este artículo.")
        return
    
    sci_hub_url = f"https://sci-hub.se/{doi}"
    
    print(f"🔎 Accediendo a: {sci_hub_url}")  
    
    try:
        response = requests.get(sci_hub_url, timeout=10)
    except requests.exceptions.Timeout:
        print("❌ Sci-Hub tardó demasiado en responder. Prueba nuevamente.")
        return
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al acceder a Sci-Hub: {e}")
        return
    
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: Sci-Hub no está accesible o el DOI es inválido.")
        return
    
    print("✅ Página cargada correctamente. Buscando enlace al PDF...")  
    
    # Analizar la página para encontrar el enlace al PDF
    soup = BeautifulSoup(response.text, "html.parser")
    iframe = soup.find("iframe")
    
    if not iframe or not iframe.get("src"):
        print("⚠ No se encontró enlace al PDF en la página.")
        print("🔍 Verifica manualmente en el navegador:", sci_hub_url)
        return

    pdf_url = iframe["src"]
    
    # Sci-Hub a veces devuelve enlaces relativos, hay que corregirlos
    if pdf_url.startswith("//"):
        pdf_url = "https:" + pdf_url

    print(f"📥 Descargando PDF desde: {pdf_url}")  
    
    try:
        pdf_response = requests.get(pdf_url, stream=True, timeout=10)
        
        if not es_pdf_valido(pdf_response):
            print(f"⚠ El enlace de Sci-Hub no devolvió un PDF válido.")
            return
        
        filename = f"{doi.replace('/', '_')}.pdf"
        with open(filename, "wb") as file:
            for chunk in pdf_response.iter_content(chunk_size=1024):
                file.write(chunk)
        
        print(f"✅ Artículo guardado desde Sci-Hub: {filename}")
    
    except requests.exceptions.Timeout:
        print("❌ La descarga del PDF tardó demasiado. Intenta nuevamente.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar el PDF: {e}")

if __name__ == "__main__":
    query = "physiotherapy AND pain"
    article_ids = buscar_articulos(query)

    for article_id in article_ids:
        article_data = obtener_detalles_articulo(article_id)
        print("\n--- PROCESANDO ARTÍCULO ---")
        print(f"Título: {article_data['title']}")
        print(f"DOI: {article_data['doi']}")
        print(f"Enlace al texto completo: {article_data['full_text_link']}")

        # Intentar descargar desde el enlace oficial primero
        if article_data["full_text_link"] != "No full text link available":
            if descargar_desde_web_oficial(article_data["full_text_link"], article_data["doi"]):
                continue  # Si se descargó, no intentar Sci-Hub

        # Si el artículo no estaba disponible gratis, probar Sci-Hub
        print("🚀 Intentando descargar desde Sci-Hub...")
        descargar_desde_scihub(article_data['doi'])
