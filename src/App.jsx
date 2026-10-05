import { useState } from "react";
import "./index.css";

import DocumentUpload from "./components/DocumentUpload.jsx";
import ChatInterface from "./components/ChatInterface.jsx";

function App() {
  const [activePage, setActivePage] = useState("home");

  return (
    <div className="app">

      {/* Sidebar */}
      <aside className="sidebar">

        {/* Logo / Brand */}
        <div className="brand">
          <div className="brand-icon">N</div>
          <h2>Nimdoc</h2>
        </div>

        {/* New Chat */}
        <button
          className="new-chat"
          onClick={() => setActivePage("chat")}
        >
          + New Chat
        </button>

        {/* Navigation */}
        <nav className="nav">

          <p
            className={activePage === "home" ? "active" : ""}
            onClick={() => setActivePage("home")}
          >
            ⌂ Home
          </p>

          <p
            className={activePage === "documents" ? "active" : ""}
            onClick={() => setActivePage("documents")}
          >
            ▣ Documents
          </p>

          <p
            className={activePage === "chat" ? "active" : ""}
            onClick={() => setActivePage("chat")}
          >
            ◌ AI Chat
          </p>

          <p
            className={activePage === "history" ? "active" : ""}
            onClick={() => setActivePage("history")}
          >
            ◷ History
          </p>

        </nav>

        {/* Bottom Navigation */}
        <div className="sidebar-bottom">

          <p onClick={() => setActivePage("settings")}>
            ⚙ Settings
          </p>

          <p>❓ Help</p>

        </div>

      </aside>

      {/* Main Content */}
      <main className="main-content">

        {/* HOME */}
        {activePage === "home" && (
          <>
            <header className="topbar">
              <div>
                <h1>Good evening 👋</h1>
                <p>What would you like to explore today?</p>
              </div>

              <div className="profile">TS</div>
            </header>

            <DocumentUpload />

            <section className="quick-section">
              <h2>Quick actions</h2>

              <div className="quick-grid">

                <div
                  className="quick-card"
                  onClick={() => setActivePage("documents")}
                >
                  <div>📄</div>
                  <h3>Documents</h3>
                  <p>
                    Upload and manage your documents.
                  </p>
                </div>

                <div
                  className="quick-card"
                  onClick={() => setActivePage("chat")}
                >
                  <div>💬</div>
                  <h3>Ask AI</h3>
                  <p>
                    Ask questions about your document.
                  </p>
                </div>

                <div className="quick-card">
                  <div>🔍</div>
                  <h3>Find Information</h3>
                  <p>
                    Search important information quickly.
                  </p>
                </div>

              </div>
            </section>
          </>
        )}

        {/* DOCUMENTS */}
        {activePage === "documents" && (
          <>
            <header className="topbar">
              <div>
                <h1>Documents</h1>
                <p>Upload your documents to Nimdoc AI.</p>
              </div>
            </header>

            <DocumentUpload />
          </>
        )}

        {/* AI CHAT */}
        {activePage === "chat" && (
          <>
            <header className="topbar">
              <div>
                <h1>AI Chat</h1>
                <p>Ask questions about your documents.</p>
              </div>
            </header>

            <ChatInterface />
          </>
        )}

        {/* HISTORY */}
        {activePage === "history" && (
          <>
            <header className="topbar">
              <div>
                <h1>History</h1>
                <p>Your previous AI conversations will appear here.</p>
              </div>
            </header>

            <div className="upload-card">
              <h2>No chat history yet</h2>
              <p>
                Your conversations will appear here once you start chatting.
              </p>
            </div>
          </>
        )}

        {/* SETTINGS */}
        {activePage === "settings" && (
          <>
            <header className="topbar">
              <div>
                <h1>Settings</h1>
                <p>Manage your Nimdoc preferences.</p>
              </div>
            </header>

            <div className="upload-card">
              <h2>Settings</h2>
              <p>
                Settings will be added here later.
              </p>
            </div>
          </>
        )}

      </main>

    </div>
  );
}

export default App;