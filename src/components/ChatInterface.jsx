import { useState } from "react";

function ChatInterface() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const handleSend = () => {
    if (!question.trim()) return;

    const userQuestion = question.trim();

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        text: userQuestion,
      },
    ]);

    setQuestion("");

    // Mock AI response for now
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          type: "ai",
          text: "This is a mock AI response. The FastAPI backend will provide the real answer later.",
          citations: ["Document page 1"],
        },
      ]);
    }, 700);
  };

  return (
    <section className="chat-container">

      <div className="chat-header">
        <h2>AI Chat</h2>
        <p>Ask questions about your uploaded document.</p>
      </div>

      <div className="chat-messages">

        {messages.length === 0 && (
          <div className="empty-chat">
            <p>Ask something about your document.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`chat-message ${message.type}`}
          >
            <div className="message-content">

              <strong>
                {message.type === "user" ? "You" : "Nimdoc AI"}
              </strong>

              <p>{message.text}</p>

              {message.citations && (
                <div className="citations">
                  <strong>Citations:</strong>

                  {message.citations.map((citation, i) => (
                    <span key={i}>{citation}</span>
                  ))}
                </div>
              )}

            </div>
          </div>
        ))}

      </div>

      <div className="chat-input-area">

        <input
          type="text"
          placeholder="Ask a question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSend();
            }
          }}
        />

        <button onClick={handleSend}>
          Send
        </button>

      </div>

    </section>
  );
}

export default ChatInterface;