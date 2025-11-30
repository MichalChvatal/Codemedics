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

  const uploadDocument = useUploadDocument();

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

      uploadDocument.mutate(payload, {
        onSuccess: () => {
          setUploading(false);
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
  baseURL: "http://localhost:8000",
});

export interface UploadedFile {
  id: string;
  url: string;
  name: string;
  size: number;
  createdAt: string;
}

async function fetchUploadedFiles(): Promise<UploadedFile[]> {
  //const res = await api.get("/uploaded-files");
  //return res.data;
}

export function useUploadedFiles() {
  return useQuery({
    queryKey: ["uploaded-files"],
    queryFn: fetchUploadedFiles,
  });
}

// --- TYPES ---
type Sender = "user" | "bot";

interface Message {
  id: number;
  message: string;
  sender: Sender;
}

// --- MOCK DATA & ICONS ---
const initialMessages: Message[] = [
  {
    id: 1,
    message: "Hello! I'm connected to your Python server.",
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
      <span
        dangerouslySetInnerHTML={{
          __html: message.message,
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
    if (!profileData[key]) continue;
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
  const [isLoading, setIsLoading] = useState<boolean>(false);

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

    // 1. Prepare user data
    const { cleaned, hasAnyFields } = cleanProfile(profile);
    const translatedProfile = translateProfile(cleaned);
    const profileInfo = JSON.stringify(translatedProfile);

    const userInfo = hasAnyFields
      ? `Uživatel s následujícími přihlašovacími údaji: ${profileInfo} odesílá následující zprávu: `
      : "";

    // The actual prompt sent to backend
    const fullPrompt = userInfo + trimmedInput;

    const userMessage: Message = {
      id: Date.now(),
      message: trimmedInput, // Display only the user text to UI, not the profile header
      sender: "user",
    };

    // 2. Update UI
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    const thinkingMessage: Message = {
      id: Date.now() + 1,
      message: "...",
      sender: "bot",
    };
    setMessages((prev) => [...prev, thinkingMessage]);

    try {
      // 3. Get Context from Local Storage
      const storedContext = localStorage.getItem("conversationContext");
      const currentContext = storedContext ? JSON.parse(storedContext) : [];

      // 4. Call Backend with Context + Prompt
      const response = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
            message: fullPrompt,
            context: currentContext
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // 5. Handle Response
      const data = await response.json();
      const botResponseText = data.message; // Assuming BE returns { response: "..." }

      // Update Local Storage with new pair
      const updatedContext = [
          ...currentContext,
          { role: "user", content: fullPrompt },
          { role: "assistant", content: botResponseText }
      ];
      localStorage.setItem("conversationContext", JSON.stringify(updatedContext));

      // Update UI Message
      setMessages((prev) => {
        const newMessages = [...prev];
        const thinkingIndex = newMessages.findIndex(
          (msg) => msg.id === thinkingMessage.id
        );

        if (thinkingIndex !== -1) {
          newMessages[thinkingIndex] = {
            ...thinkingMessage,
            message: botResponseText,
          };
        } else {
          newMessages.push({
            id: Date.now() + 2,
            message: botResponseText,
            sender: "bot",
          });
        }
        return newMessages;
      });

    } catch (error) {
      console.error("Fetch error:", error);
      setMessages((prev) => {
        const errorMessage: Message = {
          id: Date.now() + 3,
          message: `**ERROR:** Could not connect to the backend server.`,
          sender: "bot",
        };
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
      {/* --- Header --- */}
      <div className="sidebar-header">
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <h3 style={{ paddingBottom: 0, marginBottom: 0 }}>Soubory</h3>
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
              <span style={{ fontSize: "24px" }}>{getFileIcon(file.name)}</span>
              <FileLink file={file} />
            </div>
          ))}
          <FileUpload />
          <span style={{ padding: 20 }} />
          <UserProfile profile={profile} setProfile={setProfile} />
        </div>
      </div>

      {/* --- Main Chat Area --- */}
      <div className="chat-main">
        <div className="message-list">
          {messages.map((msg) => (
            <MessageComponent key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area-wrapper">
          <form onSubmit={handleSend} className="input-form">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message React TSX GPT Clone..."
              rows={1}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
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
