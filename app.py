from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient
from docx import Document
from dotenv import load_dotenv
import io  # Pour gérer les flux en mémoire

# Charger les variables d'environnement
load_dotenv()

# Configurations Azure
endpoint = os.getenv("AZURE_ENDPOINT")
api_key = os.getenv("AZURE_API_KEY")
blob_endpoint = os.getenv("AZURE_BLOB_ENDPOINT")  # Endpoint du Blob Storage
blob_container_name = os.getenv("AZURE_BLOB_CONTAINER")  # Nom du container
blob_key = os.getenv("AZURE_BLOB_KEY")  # Clé d'accès Blob

# Créer un client Azure Blob Storage
blob_service_client = BlobServiceClient(account_url=blob_endpoint, credential=blob_key)

# Créer un client Azure Document Intelligence
client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Lire le fichier PDF directement en mémoire
        pdf_stream = io.BytesIO(file.read())

        # Analyser le fichier PDF en mémoire
        result = analyze_pdf(pdf_stream)

        # Sauvegarder le résultat dans un fichier Word en mémoire
        word_stream = io.BytesIO()
        save_to_word(result, word_stream)

        # Télécharger le fichier Word directement dans Blob Storage
        blob_word_file_name = f"{file.filename.rsplit('.', 1)[0]}.docx"
        upload_word_to_blob(word_stream, blob_word_file_name)

        return jsonify({'message': 'File processed successfully', 'word_file': blob_word_file_name}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def analyze_pdf(pdf_stream):
    """Analyse le fichier PDF à partir d'un flux en mémoire."""
    poller = client.begin_analyze_document("prebuilt-document", document=pdf_stream)
    result = poller.result()
    return result


def save_to_word(result, word_stream):
    """Sauvegarde le résultat dans un fichier Word en mémoire."""
    document = Document()
    for page in result.pages:
        for line in page.lines:
            document.add_paragraph(line.content)
    document.save(word_stream)
    word_stream.seek(0)  # Réinitialiser le pointeur au début du flux


def upload_word_to_blob(word_stream, blob_word_file_name):
    """Télécharge directement un flux Word dans le Blob Storage."""
    container_client = blob_service_client.get_container_client(blob_container_name)
    blob_client = container_client.get_blob_client(blob_word_file_name)
    
    blob_client.upload_blob(word_stream, overwrite=True)
    print(f"Le fichier Word {blob_word_file_name} a été téléchargé dans le Blob Storage.")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)



# if __name__ == "__main__":
#     app.run(debug=True)
