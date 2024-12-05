import os
import logging
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from docx import Document
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Charger les paramètres d'Azure
endpoint = os.getenv("AZURE_ENDPOINT")
api_key = os.getenv("AZURE_API_KEY")
blob_endpoint = os.getenv("AZURE_BLOB_ENDPOINT")
blob_container_name = os.getenv("AZURE_BLOB_CONTAINER")
blob_key = os.getenv("AZURE_BLOB_KEY")
blob_word_file_name = "resultat.docx"

# Créer un client Azure Blob Storage
blob_service_client = BlobServiceClient(account_url=blob_endpoint, credential=blob_key)

# Créer un client Azure Document Intelligence
client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

# Fonction Blob Trigger
def main(blob: bytes, name: str):
    # Sauvegarder le fichier PDF téléchargé localement
    local_pdf_file = "/tmp/project.pdf"
    with open(local_pdf_file, "wb") as f:
        f.write(blob)
    logging.info(f"Fichier Blob {name} téléchargé sous {local_pdf_file}")

    # Analyser le PDF
    result = analyze_pdf(local_pdf_file)

    # Sauvegarder le résultat dans un fichier Word
    local_word_file = "/tmp/resultat.docx"
    save_to_word(result, local_word_file)

    # Sauvegarder le fichier Word dans Blob Storage
    upload_word_to_blob(local_word_file)

def analyze_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_document("prebuilt-document", document=f)
        result = poller.result()
    
    return result

def save_to_word(result, output_path):
    document = Document()
    for page in result.pages:
        for line in page.lines:
            document.add_paragraph(line.content)
    document.save(output_path)

def upload_word_to_blob(word_path):
    container_client = blob_service_client.get_container_client(blob_container_name)
    blob_client = container_client.get_blob_client(blob_word_file_name)
    
    with open(word_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
