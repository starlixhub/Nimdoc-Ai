import { useRef, useState } from "react";

function DocumentUpload() {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

  const handleFileSelect = (event) => {
    const file = event.target.files[0];

    if (!file) return;

    setSelectedFile(file);
    setUploadStatus("Ready to upload");
  };

  const handleUpload = () => {
    if (!selectedFile) {
      setUploadStatus("Please select a document first.");
      return;
    }

    // Mock upload for now
    // TODO: Connect this with FastAPI later
    setUploadStatus("Uploading...");

    setTimeout(() => {
      setUploadStatus("Document uploaded successfully.");
    }, 1000);
  };

  return (
    <section className="upload-card">
      <div className="upload-icon">↑</div>

      <h2>Upload your document</h2>

      <p>
        Upload a PDF or document and start asking questions with Nimdoc AI.
      </p>

      <button
        className="upload-btn"
        onClick={() => fileInputRef.current?.click()}
      >
        📁 Choose Document
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        onChange={handleFileSelect}
        hidden
      />

      {selectedFile && (
        <div className="selected-file">
          <strong>Selected:</strong> {selectedFile.name}
        </div>
      )}

      <button className="upload-btn" onClick={handleUpload}>
        Upload
      </button>

      {uploadStatus && (
        <p className="upload-status">{uploadStatus}</p>
      )}

      <span>PDF, DOCX supported</span>
    </section>
  );
}

export default DocumentUpload;