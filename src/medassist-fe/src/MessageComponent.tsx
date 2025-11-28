import React, { useState, useRef, useEffect, FC, FormEvent } from "react";
// Assuming you created this file next to Chatbot.tsx
import "./Chatbot.css";

// --- TYPES ---

type Sender = "user" | "bot";

interface Message {
  id: number;
  text: string;
  sender: Sender;
}

// --- MOCK DATA & ICONS ---

const initialMessages: Message[] = [
  {
    id: 1,
    text: "Hello! I'm a simple **TypeScript** React chatbot. How can I help you today?",
    sender: "bot",
  },
];

// Mock icon component
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

// --- MESSAGE SUB-COMPONENT ---

interface MessageProps {
  message: Message;
}

const MessageComponent: FC<MessageProps> = ({ message }) => (
  <div className={`message-container ${message.sender}`}>
    <div className={`avatar ${message.sender}`}>
      {message.sender === "user" ? "U" : "AI"}
    </div>
    <div className={`message-bubble ${message.sender}`}>
      {/* dangerouslySetInnerHTML is used here to allow the bold markdown in the initial message */}
      <span
        dangerouslySetInnerHTML={{
          __html: message.text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
        }}
      />
    </div>
  </div>
);

// --- MAIN CHATBOT COMPONENT ---

export const Chatbot: FC = () => {
  // Specify the type for the state array
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState<string>("");

  // Specify the type for the ref
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scrolls to the bottom of the message list whenever messages update
  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e: FormEvent): void => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (trimmedInput === "") return;

    const newMessage: Message = {
      id: Date.now(), // Use unique timestamp ID
      text: trimmedInput,
      sender: "user",
    };

    // 1. Add user message
    setMessages((prev) => [...prev, newMessage]);

    // 2. Clear input
    setInput("");

    // 3. Simulate bot response after a short delay
    setTimeout(() => {
      const botResponse: Message = {
        id: Date.now() + 1,
        text: `Echoing: "${trimmedInput}". This is a **mock response** from the TypeScript AI.`,
        sender: "bot",
      };
      // Use the functional update form of setMessages to ensure we use the latest state
      setMessages((prev) => [...prev, botResponse]);
    }, 1000);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    // Allows Enter key to send if Shift is not pressed
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      // TypeScript requires creating a mock FormEvent for handleSend
      handleSend(e as unknown as FormEvent);
    }
  };

  return (
    <div className="chatbot-container">
      {/* --- Header (Left Sidebar Look) --- */}
      {/* <div className="sidebar-header">
        <div className="new-chat-btn">+ New Chat</div>
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
            />
            <button
              type="submit"
              className="send-button"
              disabled={!input.trim()}
            >
              <SendIcon />
            </button>
          </form>
          <p className="disclaimer">
            This is a simplified UI clone built with TypeScript.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
