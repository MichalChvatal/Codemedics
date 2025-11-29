import React, { useState, useRef, useEffect } from "react";
import type { FormEvent, FC } from "react";
import "./Chatbot.css";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  File,
  FileImage,
  FileArchive,
  FileVideo,
  FileText,
  FileCode,
} from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { UserProfile } from "./Profile";

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: any) => {
      const res = await fetch("http://localhost:8000/upload-document", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error("Upload failed");
      }

      return res.json();
    },

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["uploaded-files"] });
    },
  });
}

function FileUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadDocument = useUploadDocument(); // <-- USE THE MUTATION HERE

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);

    const reader = new FileReader();

    reader.onload = () => {
      const base64 = reader.result.split(",")[1];

      const payload = {
        filename: file.name,
        dateOfCreation: new Date().toISOString(),
        content: base64,
      };

      // 🔥 Use the mutation instead of fetch()
      uploadDocument.mutate(payload, {
        onSuccess: () => {
          setUploading(false);

          // reset component
          setFile(null);
          if (fileInputRef.current) {
            fileInputRef.current.value = "";
          }
          toast.success("File uploaded successfully!");
        },
        onError: (err) => {
          console.error(err);
          setUploading(false);
        },
      });
    };

    reader.readAsDataURL(file);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <input type="file" onChange={handleFileChange} ref={fileInputRef} />
      {/* {file && (
        <p>
          Selected: <b>{file.name}</b>
        </p>
      )} */}

      {file && (
        <button
          onClick={handleUpload}
          disabled={!file || uploading || uploadDocument.isPending}
          style={{
            padding: "8px 14px",
            background: "#0077ff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor:
              !file || uploading || uploadDocument.isPending
                ? "default"
                : "pointer",
          }}
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>
      )}
    </div>
  );
}

const getFileIcon = (filename) => {
  const ext = filename.split(".").pop().toLowerCase();

  switch (ext) {
    case "pdf":
      return <FileText size={22} />;
    case "jpg":
    case "jpeg":
    case "png":
    case "gif":
      return <FileImage size={22} />;
    case "zip":
    case "rar":
      return <FileArchive size={22} />;
    case "mp4":
    case "mov":
      return <FileVideo size={22} />;
    case "doc":
    case "docx":
      return <FileText size={22} />;
    case "js":
    case "ts":
    case "json":
    case "html":
      return <FileCode size={22} />;
    default:
      return <File size={22} />;
  }
};

export const api = axios.create({
  baseURL: "http://localhost:8000", // 👈 default URL here
});

export interface UploadedFile {
  id: string;
  url: string;
  name: string;
  size: number;
  createdAt: string;
}

async function fetchUploadedFiles(): Promise<UploadedFile[]> {
  const res = await api.get("/uploaded-files");
  return res.data;
}

export function useUploadedFiles() {
  return useQuery({
    queryKey: ["uploaded-files"],
    queryFn: fetchUploadedFiles,
  });
}

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
    text: "Ahoj, jsem tady pro tebe, s čím potřebuješ pomoci?",
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

const FileLink = ({ file }) => {
  const [hover, setHover] = React.useState(false);

  return (
    <a
      href={file.link}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        fontSize: "18px",
        color: hover ? "gray" : "#fff",
        textDecoration: "none",
        cursor: "pointer",
      }}
    >
      {file.name}
    </a>
  );
};

const translateProfile = (profileData) => {
  const translations = {
    fullName: "Jméno a příjmení",
    personalNumber: "Osobní číslo",
    department: "Útvar / oddělení",
    contact: "Telefon / e-mail",
  };

  const translatedProfile = {};

  for (const key in profileData) {
    if (!profileData[key]) continue; // skip empty values

    const translatedKey = translations[key] || key;
    translatedProfile[translatedKey] = profileData[key];
  }

  return translatedProfile;
};

function cleanProfile(profile) {
  const cleaned = Object.fromEntries(
    Object.entries(profile).filter(([_, value]) => value && value.trim() !== "")
  );

  const hasAnyFields = Object.keys(cleaned).length > 0;

  return { cleaned, hasAnyFields };
}

const Chatbot: FC = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false); // New loading state

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const [profile, setProfile] = React.useState({
    fullName: "",
    personalNumber: "",
    department: "",
    contact: "",
  });

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (trimmedInput === "" || isLoading) return;

    const { cleaned, hasAnyFields } = cleanProfile(profile);
    const translatedProfile = translateProfile(cleaned);

    const profileInfo = JSON.stringify(translatedProfile);

    const userInfo = hasAnyFields
      ? `Uživatel s následujícími přihlašovacími údaji: ${profileInfo} odesílá následující zprávu: `
      : "";
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
        body: JSON.stringify({ message: userInfo + trimmedInput }),
      });

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

  const { data } = useUploadedFiles();

  return (
    <div className="chatbot-container">
      {/* --- Header (Left Sidebar Look) --- */}
      <div className="sidebar-header">
        {/* <div className="new-chat-btn">+ New Chat</div> */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <h3 style={{ paddingBottom: 0, marginBottom: 0 }}>Soubory</h3>
          <div style={{ maxHeight: "400px", overflowY: "auto" }}>
            {(data?.files ?? []).map((file) => (
              <div
                key={file}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "6px 0",
                }}
              >
                <span style={{ fontSize: "24px" }}>
                  {getFileIcon(file.name)}
                </span>
                <FileLink file={file} />
              </div>
            ))}
          </div>

          <FileUpload />
          <span style={{ padding: 20 }} />
          <UserProfile profile={profile} setProfile={setProfile} />
        </div>
      </div>

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
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
