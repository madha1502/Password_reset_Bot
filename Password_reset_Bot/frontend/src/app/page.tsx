"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Key,
  Send,
  RefreshCw,
  Check,
  Mail,
  Database,
  Terminal,
  User,
  Cpu,
  Clock,
  Lock,
  ChevronRight,
  Sparkles,
  Clipboard,
  ShieldCheck,
  Inbox,
  AlertCircle
} from "lucide-react";

const API_BASE_URL = "http://localhost:8000";

interface Message {
  sender: "user" | "agent";
  text: string;
  timestamp: Date;
}

interface AuditLog {
  id: number;
  email: string;
  action: string;
  timestamp: string;
}

interface MockEmail {
  id: number;
  to_email: string;
  subject: string;
  body: string;
  sent_at: string;
}

interface UserStore {
  id: number;
  email: string;
  password: string;
}

export default function Home() {
  const [sessionId, setSessionId] = useState("");
  const [currentStep, setCurrentStep] = useState("START");
  const [sessionEmail, setSessionEmail] = useState<string | null>(null);
  const [isVerified, setIsVerified] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const [activeTab, setActiveTab] = useState<"workflow" | "emails" | "database">("workflow");
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [emails, setEmails] = useState<MockEmail[]>([]);
  const [users, setUsers] = useState<UserStore[]>([]);
  
  const [selectedEmail, setSelectedEmail] = useState<MockEmail | null>(null);
  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text) return;

    if (!textToSend) setInputMessage("");

    setMessages((prev) => [...prev, { sender: "user", text, timestamp: new Date() }]);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentStep(data.current_step);
        setSessionEmail(data.email);
        setIsVerified(data.verified);
        setLastResponseStatus(data.status || null);
        setLastResponseActions(data.actions || []);

        setTimeout(() => {
          setIsTyping(false);
          setMessages((prev) => [
            ...prev,
            { sender: "agent", text: data.message, timestamp: new Date() }
          ]);
        }, 650);
      }
    } catch (err) {
      setTimeout(() => {
        setIsTyping(false);
        setMessages((prev) => [
          ...prev,
          {
            sender: "agent",
            text: "Connection failed. Please verify that the FastAPI backend server is active on port 8000.",
            timestamp: new Date()
          }
        ]);
      }, 650);
    }
  };

  const handleResetSession = () => {
    const randomId = Math.random().toString(36).substring(2, 12).toUpperCase();
    setSessionId(randomId);
    setCurrentStep("START");
    setSessionEmail(null);
    setIsVerified(false);
    setLastResponseStatus(null);
    setLastResponseActions([]);
    setMessages([
      {
        sender: "agent",
        text: "Authentication session restarted. Please describe your access issue (e.g. 'I forgot my password').",
        timestamp: new Date()
      }
    ]);
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError("");
    setRegSuccess("");
    setRegLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: regName,
          email: regEmail,
          password: regPassword
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Registration failed.");
      }

      setRegSuccess("Account created successfully!");
      setTimeout(() => {
        setShowRegisterModal(false);
        handleSendMessage("I have successfully registered my account");
      }, 1500);

    } catch (err: any) {
      setRegError(err.message || "An error occurred.");
    } finally {
      setRegLoading(false);
    }
  };

  // New state variables for registration flow
  const [copiedOtp, setCopiedOtp] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regError, setRegError] = useState("");
  const [regSuccess, setRegSuccess] = useState("");
  const [regLoading, setRegLoading] = useState(false);

  const [lastResponseStatus, setLastResponseStatus] = useState<string | null>(null);
  const [lastResponseActions, setLastResponseActions] = useState<string[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const randomId = Math.random().toString(36).substring(2, 12).toUpperCase();
    setSessionId(randomId);

    setMessages([
      {
        sender: "agent",
        text: "System initialized. I can help recover your account or reset credentials. Let me know what you need.",
        timestamp: new Date()
      }
    ]);

    fetchInspectorData();
    const interval = setInterval(fetchInspectorData, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const fetchInspectorData = async () => {
    try {
      const [logsRes, emailsRes, usersRes] = await Promise.all([
        fetch(`${API_BASE_URL}/audit-logs`),
        fetch(`${API_BASE_URL}/debug/emails`),
        fetch(`${API_BASE_URL}/debug/users`)
      ]);

      if (logsRes.ok) setAuditLogs(await logsRes.json());
      if (emailsRes.ok) setEmails(await emailsRes.json());
      if (usersRes.ok) setUsers(await usersRes.json());
    } catch (err) {
      // Backend status is handled gracefully in header via offline banner
    }
  };



  const handleSeedDatabase = async () => {
    if (!confirm("Confirm SQLite store seed reset? This will truncate transactional tables and logs.")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/debug/seed`, { method: "POST" });
      if (res.ok) {
        handleResetSession();
        fetchInspectorData();
      }
    } catch (err) {
      alert("Error reaching seed endpoint.");
    }
  };

  const handleCopyOtp = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedOtp(true);
    setTimeout(() => setCopiedOtp(false), 2000);
  };

  const isStepCompleted = (step: string) => {
    switch (step) {
      case "REQUEST":
        return currentStep !== "START";
      case "ACCOUNT":
        return sessionEmail !== null;
      case "DISPATCH":
        return ["AWAITING_OTP", "AWAITING_NEW_PASSWORD", "COMPLETED"].includes(currentStep);
      case "VERIFIED":
        return isVerified || ["AWAITING_NEW_PASSWORD", "COMPLETED"].includes(currentStep);
      case "RESET":
        return currentStep === "COMPLETED";
      default:
        return false;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#070708] text-zinc-100 antialiased selection:bg-zinc-800 font-sans">
      
      {/* Premium Dark Header Bar */}
      <header className="flex items-center justify-between px-8 py-5 border-b border-zinc-900/85 bg-[#09090b]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-b from-zinc-800 to-zinc-900 border border-zinc-700/50 flex items-center justify-center shadow-inner">
            <Key className="w-4.5 h-4.5 text-zinc-300" />
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-400">
              Identity Portal <span className="text-[10px] font-mono font-medium text-zinc-500 ml-2 border border-zinc-800 px-2 py-0.5 rounded bg-zinc-900/70 select-none">POC Sandbox</span>
            </h1>
            <p className="text-[10px] text-zinc-550 font-mono tracking-tight mt-0.5">Automated Reset Walkthrough & Audit Logs</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono text-zinc-400 bg-zinc-900/40 border border-zinc-800/80 px-2.5 py-1 rounded-md">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>API Server Connect</span>
          </div>
          <button
            onClick={handleResetSession}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs text-zinc-300 hover:text-white bg-zinc-900 hover:bg-zinc-850 rounded border border-zinc-800 hover:border-zinc-700 transition duration-200 font-medium"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Flow
          </button>
        </div>
      </header>

      {/* Primary Split Viewport */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden h-[calc(100vh-77px)]">
        
        {/* LEFT COLUMN: Helpdesk Interactive Chat Widget */}
        <section className="lg:col-span-5 flex flex-col bg-[#070708] border-r border-zinc-900/90 h-full justify-between">
          <div className="px-6 py-4 border-b border-zinc-900/90 flex justify-between items-center bg-[#09090b]/40">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-zinc-500" /> Conversational Agent
            </span>
            <span className="text-[10px] font-mono text-zinc-650 bg-zinc-900/20 px-2 py-0.5 rounded border border-zinc-850/60">SESSION_{sessionId}</span>
          </div>

          {/* Chat Messages Frame */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6 max-h-[calc(100vh-230px)] scrollbar-thin">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3.5 max-w-[85%] ${
                  msg.sender === "user" ? "ml-auto flex-row-reverse" : ""
                }`}
              >
                <div
                  className={`w-7.5 h-7.5 rounded-md flex items-center justify-center text-[10px] shrink-0 font-semibold border transition duration-200 select-none ${
                    msg.sender === "user"
                      ? "bg-zinc-900 border-zinc-750 text-zinc-200"
                      : "bg-[#09090b] border-zinc-850 text-zinc-400"
                  }`}
                >
                  {msg.sender === "user" ? <User className="w-3.5 h-3.5 text-zinc-300" /> : <Sparkles className="w-3.5 h-3.5 text-zinc-550" />}
                </div>
                <div className="space-y-1.5">
                  <div
                    className={`px-4 py-3 rounded-lg text-xs leading-relaxed border shadow-sm ${
                      msg.sender === "user"
                        ? "bg-zinc-900/40 text-zinc-150 border-zinc-800"
                        : "bg-zinc-950/20 text-zinc-300 border-zinc-900/90"
                    }`}
                  >
                    {msg.text}
                  </div>
                  <div className="text-[9px] text-zinc-600 px-1 font-mono tracking-tight">
                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3.5 max-w-[85%]">
                <div className="w-7.5 h-7.5 rounded-md border border-zinc-900/80 bg-zinc-950 flex items-center justify-center text-[10px] text-zinc-600">
                  <Cpu className="w-3.5 h-3.5 text-zinc-750 animate-pulse" />
                </div>
                <div className="flex items-center gap-1.5 bg-zinc-950/20 border border-zinc-900/80 px-4 py-2.5 rounded-lg shadow-sm">
                  <span className="w-1.5 h-1.5 bg-zinc-550 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 bg-zinc-550 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-zinc-550 rounded-full animate-bounce"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick chips & Form */}
          <div className="p-6 border-t border-zinc-900/90 bg-[#09090b]/20">
            {messages.length === 1 && (
              <div className="mb-4">
                <p className="text-[9px] text-zinc-550 font-bold tracking-wider uppercase mb-2">Select Account Action</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleSendMessage("I forgot my password")}
                    className="text-[11px] bg-zinc-900/50 hover:bg-zinc-850 hover:text-white text-zinc-400 border border-zinc-800/80 hover:border-zinc-750 px-3 py-1.5 rounded-md transition duration-200 flex items-center gap-1.5"
                  >
                    <span>I forgot my password</span>
                    <ChevronRight className="w-3 h-3 text-zinc-600" />
                  </button>
                  <button
                    onClick={() => handleSendMessage("Reset my account")}
                    className="text-[11px] bg-zinc-900/50 hover:bg-zinc-850 hover:text-white text-zinc-400 border border-zinc-800/80 hover:border-zinc-750 px-3 py-1.5 rounded-md transition duration-200 flex items-center gap-1.5"
                  >
                    <span>Reset my account</span>
                    <ChevronRight className="w-3 h-3 text-zinc-600" />
                  </button>
                </div>
              </div>
            )}

            {currentStep === "AWAITING_REGISTRATION_CHOICE" && (
              <div className="mb-4">
                <p className="text-[9px] text-zinc-550 font-bold tracking-wider uppercase mb-2">Options</p>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setRegEmail(sessionEmail || "");
                      setRegName("");
                      setRegPassword("");
                      setRegError("");
                      setRegSuccess("");
                      setShowRegisterModal(true);
                    }}
                    className="text-[11px] bg-emerald-950/40 hover:bg-emerald-900/60 hover:text-white text-emerald-400 border border-emerald-900/80 hover:border-emerald-700 px-4 py-2 rounded-md transition duration-200 flex items-center gap-1.5 font-medium shadow-sm cursor-pointer"
                  >
                    <span>Register New User</span>
                    <ChevronRight className="w-3 h-3 text-emerald-500" />
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSendMessage("Use Another Email")}
                    className="text-[11px] bg-zinc-900/50 hover:bg-zinc-850 hover:text-white text-zinc-400 border border-zinc-800/80 hover:border-zinc-750 px-4 py-2 rounded-md transition duration-200 flex items-center gap-1.5 font-medium cursor-pointer"
                  >
                    <span>Use Another Email</span>
                    <ChevronRight className="w-3 h-3 text-zinc-650" />
                  </button>
                </div>
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="relative flex items-center"
            >
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={
                  currentStep === "AWAITING_EMAIL"
                    ? "Enter registered email (e.g. user@example.com)..."
                    : currentStep === "AWAITING_OTP"
                    ? "Enter 6-digit verification code..."
                    : currentStep === "AWAITING_NEW_PASSWORD"
                    ? "Enter your new credentials (min 6 chars)..."
                    : currentStep === "AWAITING_REGISTRATION_NAME"
                    ? "Enter your full name..."
                    : currentStep === "AWAITING_REGISTRATION_EMAIL"
                    ? "Enter your email address..."
                    : currentStep === "AWAITING_REGISTRATION_PASSWORD"
                    ? "Choose a secure password (min 6 chars)..."
                    : "Ask support bot..."
                }
                className="w-full bg-[#09090b] border border-zinc-850 focus:border-zinc-750 focus:outline-none rounded-lg py-3 pl-4.5 pr-12 text-xs text-zinc-200 placeholder-zinc-550 transition font-mono tracking-tight"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim()}
                className="absolute right-2 p-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-350 hover:text-white disabled:opacity-45 transition duration-150 cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </section>

        {/* RIGHT COLUMN: Premium Segmented Inspector Console */}
        <section className="lg:col-span-7 flex flex-col bg-[#09090b]/15 h-full overflow-hidden">
          
          {/* Header Segment Controls */}
          <div className="px-6 py-4.5 border-b border-zinc-900/90 flex justify-between items-center bg-[#09090b]/80">
            <div className="bg-zinc-900/60 p-0.5 rounded-lg border border-zinc-850/80 flex gap-1 shadow-inner select-none">
              {[
                { id: "workflow", label: "State Monitor", icon: Terminal },
                { id: "emails", label: "Email Logs", icon: Mail },
                { id: "database", label: "User Store", icon: Database }
              ].map((tab) => {
                const Icon = tab.icon;
                const isSelected = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium tracking-wide transition duration-150 cursor-pointer ${
                      isSelected
                        ? "bg-zinc-850 text-white shadow-sm border border-zinc-800/80 font-semibold"
                        : "text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {tab.label}
                    {tab.id === "emails" && emails.length > 0 && (
                      <span className="px-1.5 py-0.5 text-[9px] font-bold bg-zinc-800 border border-zinc-750 text-zinc-300 rounded ml-1 font-mono leading-none">
                        {emails.length}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            
            <span className="text-[10px] font-mono text-zinc-550 tracking-wider uppercase border border-zinc-900 px-2 py-0.5 rounded bg-zinc-950/20">SQLite DB</span>
          </div>

          {/* Detailed Dashboard Area */}
          <div className="flex-1 overflow-y-auto p-6 scrollbar-thin space-y-6">
            
            {/* TAB 1: STATE MONITOR & TIMELINE */}
            {activeTab === "workflow" && (
              <div className="space-y-6">
                
                {/* Stepper tracker */}
                <div className="bg-zinc-900/15 border border-zinc-900/95 rounded-lg p-6 backdrop-blur-md">
                  <div className="flex items-center gap-2 mb-6 text-zinc-400">
                    <ShieldCheck className="w-4 h-4" />
                    <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Reset Process Tracker</h3>
                  </div>

                  <div className="relative pl-6 space-y-6 border-l border-zinc-900">
                    {[
                      { step: "REQUEST", label: "RESET_REQUESTED", desc: "User request password recovery session." },
                      { step: "ACCOUNT", label: "USER_FOUND", desc: "Target email verified. Identity matched." },
                      { step: "DISPATCH", label: "OTP_SENT", desc: "OTP code created and dispatched via mock SMTP server." },
                      { step: "VERIFIED", label: "OTP_VERIFIED", desc: "User input OTP matches database active record." },
                      { step: "RESET", label: "PASSWORD_RESET", desc: "Credentials successfully updated and SHA-256 hashed." }
                    ].map((row, index) => {
                      const done = isStepCompleted(row.step);
                      return (
                        <div key={index} className="relative group">
                          {/* Stepper Connector Dot */}
                          <div
                            className={`absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full flex items-center justify-center transition duration-200 border ${
                              done
                                ? "bg-zinc-200 border-zinc-150 text-zinc-950 shadow-md shadow-zinc-150/10"
                                : "bg-zinc-950 border-zinc-850 text-zinc-650"
                            }`}
                          >
                            {done && <Check className="w-2.5 h-2.5 stroke-[3.5]" />}
                          </div>
                          
                          <div>
                            <h4
                              className={`text-[11px] font-semibold tracking-wide font-mono transition duration-200 ${
                                done ? "text-zinc-200" : "text-zinc-600"
                              }`}
                            >
                              {row.label}
                            </h4>
                            <p className="text-[10px] text-zinc-550 mt-0.5">{row.desc}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* macOS Style Code Terminal wrapper */}
                <div className="bg-[#09090b] border border-zinc-900/90 rounded-lg overflow-hidden flex flex-col font-mono text-[11px] shadow-lg">
                  <div className="px-4 py-3 bg-zinc-900/40 border-b border-zinc-900 flex justify-between items-center text-zinc-550 select-none">
                    <div className="flex items-center gap-4">
                      {/* macOS buttons */}
                      <div className="flex gap-1.5 shrink-0">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500/30 border border-red-500/20"></span>
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/30 border border-yellow-500/20"></span>
                        <span className="w-2.5 h-2.5 rounded-full bg-green-500/30 border border-green-500/20"></span>
                      </div>
                      <span className="text-[10px] uppercase font-bold tracking-wider flex items-center gap-1.5 font-sans">
                        <Terminal className="w-3.5 h-3.5 text-zinc-500" /> Transactional Logs
                      </span>
                    </div>
                    <span className="text-[9px] font-semibold text-zinc-600">stdout</span>
                  </div>

                  <div className="p-4 space-y-1.5 max-h-[240px] overflow-y-auto scrollbar-thin text-zinc-450">
                    {auditLogs.length === 0 ? (
                      <div className="text-center py-4 text-zinc-600 text-[10px] italic">
                        [MONITOR]: System idle. Send message in chat to start logs...
                      </div>
                    ) : (
                      auditLogs.map((log) => {
                        const date = new Date(log.timestamp);
                        const isSuccess = !log.action.includes("FAILED") && !log.action.includes("UNAUTHORIZED");
                        return (
                          <div key={log.id} className="hover:bg-zinc-900/20 py-0.5 px-1 rounded transition duration-100 flex justify-between gap-4">
                            <span className="shrink-0 text-zinc-600 select-none">
                              {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </span>
                            <span
                              className={`font-semibold text-left flex-1 ${
                                isSuccess ? "text-zinc-300" : "text-rose-500"
                              }`}
                            >
                              {log.action}
                            </span>
                            <span className="text-zinc-500 truncate max-w-[190px]">&lt;{log.email}&gt;</span>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

              </div>
            )}

            {/* TAB 2: TRANSACTIONAL EMAIL LOGS */}
            {activeTab === "emails" && (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-5 h-[calc(100vh-220px)] overflow-hidden">
                
                {/* Email Transmissions list */}
                <div className="md:col-span-5 flex flex-col bg-[#09090b]/30 border border-zinc-900 rounded-lg overflow-hidden h-full">
                  <div className="px-4 py-2.5 bg-zinc-900/30 border-b border-zinc-900 flex justify-between items-center text-[10px] text-zinc-500 select-none">
                    <span className="font-semibold uppercase tracking-wider">Email Sink</span>
                    <span className="bg-zinc-850 px-2 py-0.5 rounded text-[9px] text-zinc-400 font-mono">{emails.length} queued</span>
                  </div>
                  
                  <div className="flex-1 overflow-y-auto divide-y divide-zinc-900 scrollbar-thin">
                    {emails.length === 0 ? (
                      <div className="p-6 text-center text-zinc-600 text-xs italic">
                        Mail queue empty. Trigger password reset workflow to dispatch OTP.
                      </div>
                    ) : (
                      emails.map((email) => {
                        const date = new Date(email.sent_at);
                        const isSelected = selectedEmail?.id === email.id;
                        const otpMatch = email.body.match(/=== OTP CODE ===\r?\n(\d{6})/);
                        const otpCode = otpMatch ? otpMatch[1] : null;

                        return (
                          <div
                            key={email.id}
                            onClick={() => setSelectedEmail(email)}
                            className={`p-3 text-left cursor-pointer transition select-none text-xs flex flex-col gap-1 border-l-2 ${
                              isSelected
                                ? "bg-zinc-900/70 border-zinc-200"
                                : "hover:bg-zinc-900/20 border-transparent"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-zinc-300 truncate max-w-[100px]">{email.to_email}</span>
                              <span className="text-[9px] text-zinc-650 font-mono">
                                {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                            <div className="text-[10px] text-zinc-500 truncate">{email.subject}</div>
                            {otpCode && (
                              <div className="self-start mt-1 px-1.5 py-0.5 bg-zinc-900 text-zinc-400 rounded border border-zinc-850 text-[9px] font-mono select-none">
                                CODE: {otpCode}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>

                {/* Email Viewer (Mock Browser Interface) */}
                <div className="md:col-span-7 flex flex-col bg-[#09090b]/30 border border-zinc-900 rounded-lg overflow-hidden h-full">
                  {selectedEmail ? (
                    <div className="flex flex-col h-full bg-[#070708]/30">
                      
                      {/* Browser address bar detail */}
                      <div className="p-4 bg-zinc-900/30 border-b border-zinc-900 flex flex-col gap-1.5">
                        <div className="flex items-center gap-1.5 text-[9px] font-mono text-zinc-500">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          <span>SMTP SSL Delivery Completed</span>
                        </div>
                        <div className="space-y-0.5 text-[10px] font-mono text-zinc-550">
                          <p><span className="text-zinc-600 font-sans">From:</span> support@company.com</p>
                          <p><span className="text-zinc-600 font-sans">To:</span> {selectedEmail.to_email}</p>
                          <p className="text-xs font-semibold text-zinc-350 font-sans pt-1.5">{selectedEmail.subject}</p>
                        </div>
                      </div>
                      
                      {/* Body area */}
                      <div className="flex-1 p-5 overflow-y-auto font-mono text-[11px] text-zinc-400 leading-relaxed whitespace-pre-wrap select-text scrollbar-thin">
                        {selectedEmail.body}
                        
                        {(() => {
                          const otpMatch = selectedEmail.body.match(/=== OTP CODE ===\r?\n(\d{6})/);
                          const otpCode = otpMatch ? otpMatch[1] : null;
                          if (otpCode) {
                            return (
                              <div className="mt-6 p-4 rounded border border-zinc-850 bg-zinc-900/20 flex items-center justify-between font-sans">
                                <div>
                                  <p className="text-[9px] text-zinc-550 font-bold uppercase tracking-wider">Payload Token</p>
                                  <p className="text-base font-bold text-zinc-200 tracking-widest font-mono mt-0.5">{otpCode}</p>
                                </div>
                                <button
                                  onClick={() => handleCopyOtp(otpCode)}
                                  className="flex items-center gap-1 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-850 hover:text-white border border-zinc-800 hover:border-zinc-700 text-zinc-300 rounded text-xs transition duration-150 cursor-pointer"
                                >
                                  {copiedOtp ? (
                                    <>
                                      <Check className="w-3 h-3 text-emerald-400" />
                                      Copied
                                    </>
                                  ) : (
                                    <>
                                      <Clipboard className="w-3.5 h-3.5 text-zinc-500" />
                                      Copy OTP
                                    </>
                                  )}
                                </button>
                              </div>
                            );
                          }
                          return null;
                        })()}
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-zinc-650 text-xs p-6 text-center">
                      <Inbox className="w-8 h-8 text-zinc-750 mb-2.5 animate-pulse" />
                      <p>Select a transmission to view its envelope header, verification payload, and copy parameters.</p>
                    </div>
                  )}
                </div>

              </div>
            )}

            {/* TAB 3: USER SQL DATABASE STORE */}
            {activeTab === "database" && (
              <div className="space-y-6">
                
                {/* SQLite Store controller */}
                <div className="bg-zinc-900/15 border border-zinc-900 rounded-lg p-5 flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-zinc-200 tracking-wide uppercase tracking-wider flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-zinc-500" />
                      SQLite Database State
                    </h3>
                    <p className="text-[10px] text-zinc-550 mt-0.5">Mock tables showing current credential hashes.</p>
                  </div>
                  <button
                    onClick={handleSeedDatabase}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-850 border border-zinc-800 hover:border-zinc-750 text-zinc-300 hover:text-white rounded text-xs font-medium transition duration-200"
                  >
                    Reseed Users
                  </button>
                </div>

                {/* Database Table layout */}
                <div className="bg-[#09090b] border border-zinc-900/90 rounded-lg overflow-hidden shadow-lg">
                  <div className="px-4 py-3.5 bg-zinc-900/40 border-b border-zinc-900 flex justify-between items-center text-[10px] text-zinc-550 select-none">
                    <span className="font-semibold uppercase tracking-wider font-mono">TABLE users</span>
                    <span className="font-mono text-zinc-600">engine: sqlite3_v3.x</span>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-zinc-900/10 border-b border-zinc-900 text-[10px] text-zinc-500 font-mono">
                          <th className="px-5 py-3">id</th>
                          <th className="px-5 py-3">name</th>
                          <th className="px-5 py-3">email</th>
                          <th className="px-5 py-3">password_hash (sha256)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-900 text-[11px] font-mono text-zinc-400">
                        {users.map((u: any) => (
                          <tr key={u.id} className="hover:bg-zinc-900/10 transition">
                            <td className="px-5 py-3 text-zinc-650">{u.id}</td>
                            <td className="px-5 py-3 text-zinc-250 font-sans text-xs">{u.name || "N/A"}</td>
                            <td className="px-5 py-3 text-zinc-250 font-sans text-xs">{u.email}</td>
                            <td className="px-5 py-3">
                              <div className="flex items-center gap-2 max-w-[280px]">
                                <Lock className="w-3.5 h-3.5 text-zinc-800 shrink-0" />
                                <span className="truncate tracking-tight text-[10px] text-zinc-550" title={u.password_hash}>
                                  {u.password_hash}
                                </span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Sandbox explanation note */}
                <div className="p-4 rounded border border-zinc-900 bg-zinc-900/10 text-[10px] text-zinc-550 leading-relaxed flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-zinc-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-zinc-400 font-sans mb-0.5">Real-time Credential Validation</p>
                    <p>
                      The database writes are persistent across the current session lifecycle. When you perform a password update using the Helpdesk Assistant, the change triggers an SQL UPDATE transaction, causing the SHA-256 hash to modify instantly.
                    </p>
                  </div>
                </div>

              </div>
            )}

          </div>
        </section>
      </main>

      {/* Status Footer */}
      <footer className="px-8 py-3.5 border-t border-zinc-900 bg-zinc-950 text-[9px] text-zinc-600 flex items-center justify-between font-mono select-none">
        <div>
          <span>Runtime: Python FastAPI + Next.js App Router</span>
        </div>
        <div className="flex items-center gap-3">
          <span>Ollama/Llama 3.2 Detection: Auto-Fallback Enabled</span>
        </div>
      </footer>

      {showRegisterModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
          <div className="w-full max-w-md bg-[#09090b] border border-zinc-800 rounded-xl overflow-hidden shadow-2xl flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4.5 border-b border-zinc-900 flex justify-between items-center bg-zinc-950/40">
              <span className="text-xs font-semibold uppercase tracking-wider text-zinc-200 flex items-center gap-2">
                <User className="w-4 h-4 text-zinc-450" /> Register New Account
              </span>
              <button
                type="button"
                onClick={() => setShowRegisterModal(false)}
                className="text-zinc-500 hover:text-zinc-350 text-sm transition font-mono cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleRegisterSubmit} className="p-6 space-y-4 text-xs">
              {regError && (
                <div className="p-3 bg-red-955/20 border border-red-900/60 text-red-400 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{regError}</span>
                </div>
              )}
              {regSuccess && (
                <div className="p-3 bg-emerald-955/20 border border-emerald-900/60 text-emerald-400 rounded-lg flex items-start gap-2">
                  <Check className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{regSuccess}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Full Name</label>
                <input
                  type="text"
                  required
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  placeholder="e.g. John Doe"
                  className="w-full bg-zinc-900/40 border border-zinc-805 focus:border-zinc-700 focus:outline-none rounded-lg py-2.5 px-3.5 text-zinc-200 placeholder-zinc-600 transition"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Email Address</label>
                <input
                  type="email"
                  required
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="e.g. name@company.com"
                  className="w-full bg-zinc-900/40 border border-zinc-805 focus:border-zinc-700 focus:outline-none rounded-lg py-2.5 px-3.5 text-zinc-200 placeholder-zinc-600 transition"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Password</label>
                <input
                  type="password"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  className="w-full bg-zinc-900/40 border border-zinc-805 focus:border-zinc-700 focus:outline-none rounded-lg py-2.5 px-3.5 text-zinc-200 placeholder-zinc-600 transition font-mono"
                />
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 text-zinc-400 hover:text-white bg-zinc-900 hover:bg-zinc-850 rounded-lg border border-zinc-800 transition duration-150 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={regLoading}
                  className="px-5 py-2 text-zinc-950 font-semibold bg-zinc-200 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-md transition duration-150 cursor-pointer"
                >
                  {regLoading ? "Registering..." : "Create Account"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
