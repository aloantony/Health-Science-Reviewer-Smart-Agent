import requests
import xml.etree.ElementTree as ET

def buscar_articulos(pubmed_query, max_results=5):
    """Busca artículos en PubMed y devuelve una lista de IDs"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": pubmed_query,
        "retmode": "xml",
        "retmax": max_results
    }
    
    response = requests.get(base_url, params=params)
    root = ET.fromstring(response.text)

    article_ids = [id_elem.text for id_elem in root.findall(".//Id")]
    return article_ids

def obtener_detalles_articulo(article_id):
    """Obtiene título, autores, resumen, DOI y enlace al texto completo"""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": article_id, "retmode": "xml"}
    
    response = requests.get(url, params=params)
    root = ET.fromstring(response.text)
    
    title_elem = root.find(".//ArticleTitle")
    title = title_elem.text if title_elem is not None else "No title available"

    abstract_elem = root.find(".//AbstractText")
    abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"

    authors = []
    for author in root.findall(".//Author"):
        last_name = author.find("LastName")
        fore_name = author.find("ForeName")
        if last_name is not None and fore_name is not None:
            authors.append(f"{fore_name.text} {last_name.text}")

    # Buscar el DOI del artículo
    doi = "No DOI available"
    for elocation in root.findall(".//ELocationID"):
        if elocation.attrib.get("EIdType") == "doi":
            doi = elocation.text
            break

    # Buscar enlace al texto completo en PubMed Central o en la web de la revista
    full_text_link = "No full text link available"
    for link in root.findall(".//ArticleIdList/ArticleId"):
        if link.attrib.get("IdType") == "pmc":  # PubMed Central suele ser acceso abierto
            full_text_link = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{link.text}/"
            break
        if link.attrib.get("IdType") == "doi":  # DOI suele redirigir a la web oficial
            full_text_link = f"https://doi.org/{link.text}"
            break

    return {
        "id": article_id,
        "title": title,
        "authors": ", ".join(authors) if authors else "No authors available",
        "abstract": abstract,
        "doi": doi,
        "full_text_link": full_text_link
    }
