document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a PDF file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://127.0.0.1:5000/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        if (response.ok) {
            console.log(result); // Affiche la réponse dans la console
            document.getElementById('output').innerText = `Word file created: ${result.word_file}`;
        } else {
            console.error(result); // Affiche une erreur dans la console
            document.getElementById('output').innerText = `Error: ${result.error}`;
        }
    } catch (error) {
        console.error(error); // Affiche une erreur réseau ou autre
        document.getElementById('output').innerText = `Error: ${error.message}`;
    }
});
