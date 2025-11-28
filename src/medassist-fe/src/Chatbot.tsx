import React, { useState, useRef, useEffect, FC, FormEvent } from "react";
import "./Chatbot.css";

// --- TYPES (Same as before) ---
type Sender = "user" | "bot";

interface Message {
  id: number;
  text: string;
  sender: Sender;
}

// --- MOCK DATA & ICONS (Same as before) ---
const initialMessages: Message[] = [
  {
    id: 1,
    text: "Hello! I'm connected to your Python server. Send a message to see it returned in **UPPERCASE**.",
    sender: "bot",
  },
];

const SendIcon: FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="send-icon"
  >
    <path d="M3.477 14.88c.198.397.63.518.995.385l16.148-5.768a.715.715 0 0 0 .193-1.354L4.472 4.095c-.37-.133-.797-.015-.995.385-.205.418-.088.94.316 1.144l4.312 2.156-4.312 2.156c-.404.204-.521.726-.316 1.144Z" />
  </svg>
);

// --- MESSAGE SUB-COMPONENT (Same as before) ---
interface MessageProps {
  message: Message;
}

const MessageComponent: FC<MessageProps> = ({ message }) => (
  <div className={`message-container ${message.sender}`}>
    <div className={`avatar ${message.sender}`}>
      {message.sender === "user" ? "U" : "AI"}
    </div>
    <div className={`message-bubble ${message.sender}`}>
      <span
        dangerouslySetInnerHTML={{
          __html: message.text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
        }}
      />
    </div>
  </div>
);

// --- MAIN CHATBOT COMPONENT ---

const Chatbot: FC = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false); // New loading state

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (trimmedInput === "" || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: trimmedInput,
      sender: "user",
    };

    // 1. Add user message and set loading
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // 2. Prepare bot response placeholder (optional, but good for UI feedback)
    const thinkingMessage: Message = {
      id: Date.now() + 1,
      text: "...",
      sender: "bot",
    };
    setMessages((prev) => [...prev, thinkingMessage]);

    try {
      // --- BACKEND API CALL ---
      const response = await fetch("http://localhost:8000", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // Send the message in JSON format as expected by your Python server
        body: JSON.stringify({ message: trimmedInput }),
      });
      console.log("the response is ", response);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: { message: string } = await response.json();

      // 3. Update the last (thinking) message with the actual response
      setMessages((prev) => {
        // Find the thinking message and replace it
        const newMessages = [...prev];
        const thinkingIndex = newMessages.findIndex(
          (msg) => msg.id === thinkingMessage.id
        );

        if (thinkingIndex !== -1) {
          newMessages[thinkingIndex] = {
            ...thinkingMessage,
            text: data.message, // The UPPERCASE message from the BE
          };
        } else {
          // If somehow the thinking message wasn't found, just append the new one
          newMessages.push({
            id: Date.now() + 2,
            text: data.message,
            sender: "bot",
          });
        }
        return newMessages;
      });
    } catch (error) {
      console.error("Fetch error:", error);
      // Display error message to the user
      setMessages((prev) => {
        const errorMessage: Message = {
          id: Date.now() + 3,
          text: `**ERROR:** Could not connect to the backend server. Is the Python server running on **http://localhost:8000**?`,
          sender: "bot",
        };
        // Remove the 'thinking' message and add the error
        const filtered = prev.filter((msg) => msg.id !== thinkingMessage.id);
        return [...filtered, errorMessage];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e as unknown as FormEvent);
    }
  };

  return (
    <div className="chatbot-container">
      {/* --- Header (Left Sidebar Look) --- */}
      {/* <div className="sidebar-header">
        <div className="new-chat-btn">+ New Chat</div>
        <div className="title">React TSX / Python Chat</div>
      </div> */}

      {/* --- Main Chat Area --- */}
      <div className="chat-main">
        {/* --- Message Display --- */}
        <div className="message-list">
          {messages.map((msg) => (
            <MessageComponent key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} /> {/* Scroll target */}
        </div>

        {/* --- Input Area --- */}
        <div className="input-area-wrapper">
          <form onSubmit={handleSend} className="input-form">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message React TSX GPT Clone..."
              rows={1}
              onKeyDown={handleKeyDown}
              disabled={isLoading} // Disable input while waiting for response
            />
            <button
              type="submit"
              className="send-button"
              disabled={!input.trim() || isLoading}
            >
              <SendIcon />
            </button>
          </form>
          <p className="disclaimer">
            This UI communicates with your Python server on **port 8000**.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
