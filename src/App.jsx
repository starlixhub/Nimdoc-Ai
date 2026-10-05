import { useRef, useState } from "react";
import "./index.css";

function App() {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];

    if (file) {
      setSelectedFile(file);
    }
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">N</div>
          <h2>Nimdoc</h2>
        </div>

        <button className="new-chat">+ New Chat</button>

        <nav className="nav">
          <p className="active">⌂ Home</p>
          <p>▣ Documents</p>
          <p>◌ AI Chat</p>
          <p>◷ History</p>
        </nav>

        <div className="sidebar-bottom">
          <p>⚙ Settings</p>
          <p>? Help</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>Good evening 👋</h1>
            <p>What would you like to explore today?</p>
          </div>

          <div className="profile">TS</div>
        </header>

        {/* Upload */}
        <section className="upload-card">
          <div className="upload-icon">↑</div>

          <h2>Upload your document</h2>

          <p>
            Upload a PDF or document and start asking questions with Nimdoc AI.
          </p>

          <button
            className="upload-btn"
            onClick={() => fileInputRef.current.click()}
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
            <p className="selected-file">
              Selected: {selectedFile.name}
            </p>
          )}

          <span>PDF, DOCX supported</span>
        </section>

        {/* Quick Actions */}
        <section className="quick-section">
          <h2>Quick actions</h2>

          <div className="quick-grid">
            <div className="quick-card">
              <div>📄</div>
              <h3>Summarize</h3>
              <p>Get a quick summary of your document.</p>
            </div>

            <div className="quick-card">
              <div>💬</div>
              <h3>Ask AI</h3>
              <p>Ask questions directly from your document.</p>
            </div>

            <div className="quick-card">
              <div>🔍</div>
              <h3>Find Information</h3>
              <p>Search important information quickly.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;