"use client";

import { useState, useEffect, useRef } from "react";
import { chatAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Bot,
  User,
  Plus,
  MessageSquare,
  Sparkles,
  Trash2,
  Clock,
} from "lucide-react";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: string;
}

interface Session {
  sessionId: string;
  title?: string;
  model?: string;
  createdAt: string;
  lastMessageAt?: string;
  updatedAt?: string;
  counters?: {
    messages: number;
    tokensIn: number;
    tokensOut: number;
  };
  messages?: Message[];
}

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
    loadModels();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadSessions = async () => {
    try {
      const response = await chatAPI.getSessions();
      const sessionsData = response.data || [];

      // Load messages for each session to get the title from first message
      const sessionsWithMessages = await Promise.all(
        sessionsData.map(async (session: Session) => {
          try {
            const sessionResponse = await chatAPI.getSession(session.sessionId);
            const messages = sessionResponse.data.messages || [];
            const firstUserMessage = messages.find(
              (msg: Message) => msg.role === "user"
            );

            return {
              ...session,
              messages,
              title: firstUserMessage
                ? firstUserMessage.content.substring(0, 50) +
                  (firstUserMessage.content.length > 50 ? "..." : "")
                : "Nueva Conversación",
            };
          } catch (error) {
            console.error(
              `Failed to load session ${session.sessionId}:`,
              error
            );
            return {
              ...session,
              title: "Chat sin título",
            };
          }
        })
      );

      setSessions(sessionsWithMessages);

      // Load first session if available
      if (
        sessionsWithMessages.length > 0 &&
        sessionsWithMessages[0]?.sessionId
      ) {
        const firstSession = sessionsWithMessages[0];
        setMessages(firstSession.messages || []);
        setCurrentSessionId(firstSession.sessionId);
      }
    } catch (error) {
      console.error("Failed to load sessions:", error);
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadModels = async () => {
    try {
      const response = await chatAPI.getModels();
      // Handle both array and object with models property
      let modelsData = Array.isArray(response.data)
        ? response.data
        : response.data?.models || [];

      // Ensure all models are strings (handle if they're objects)
      modelsData = modelsData.map((model: any) => {
        if (typeof model === "string") return model;
        if (typeof model === "object" && model !== null) {
          return model.id || model.name || model.model || JSON.stringify(model);
        }
        return String(model);
      });

      setModels(modelsData);
    } catch (error) {
      console.error("Failed to load models:", error);
      // Set default models as fallback
      setModels(["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]);
    }
  };

  const loadSession = async (sessionId: string) => {
    if (!sessionId) {
      console.error("Session ID is required");
      return;
    }

    try {
      const response = await chatAPI.getSession(sessionId);
      setMessages(response.data.messages || []);
      setCurrentSessionId(sessionId);
    } catch (error: any) {
      console.error("Failed to load session:", error);
      console.error("Session ID:", sessionId);
      console.error("Error details:", error.response?.data);
      toast.error("Failed to load session");
    }
  };

  const createNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userMessage = message;
    setMessage("");
    setLoading(true);

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: Date.now().toString(),
      content: userMessage,
      role: "user",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const response = await chatAPI.sendMessage({
        message: userMessage,
        sessionId: currentSessionId || undefined,
        model: selectedModel,
      });

      // Update session ID if new session was created
      if (!currentSessionId && response.data.session_id) {
        setCurrentSessionId(response.data.session_id);
        loadSessions(); // Reload sessions list
      }

      // Add assistant message
      const assistantMessage: Message = {
        id: response.data.id || Date.now().toString(),
        content: response.data.content || response.data.response,
        role: "assistant",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      toast.success("Message sent!");
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to send message");
      // Remove the temporary user message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-12rem)]">
      {/* Sessions Sidebar */}
      <motion.div
        initial={{ x: -50, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="lg:col-span-1 h-full"
      >
        <Card className="h-full border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg overflow-hidden !p-0">
          <CardHeader className="border-b dark:border-gray-700/50 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MessageSquare className="h-5 w-5 text-blue-500" />
                <CardTitle className="text-lg">Conversaciones</CardTitle>
              </div>
              <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={createNewSession}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 text-white border-0 hover:opacity-90"
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </motion.div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <ScrollArea className="h-[calc(100vh-20rem)]">
              {loadingSessions ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-20 w-full rounded-xl" />
                  ))}
                </div>
              ) : sessions.length === 0 ? (
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="text-center text-muted-foreground py-8"
                >
                  <MessageSquare className="h-16 w-16 mx-auto mb-3 opacity-30 dark:opacity-20" />
                  <p className="text-sm font-medium">No hay conversaciones</p>
                  <p className="text-xs mt-1">Crea una nueva para comenzar</p>
                </motion.div>
              ) : (
                <div className="space-y-2">
                  <AnimatePresence>
                    {sessions.map((session, index) => {
                      const isActive = currentSessionId === session.sessionId;
                      const date = new Date(session.createdAt);

                      return (
                        <motion.div
                          key={session.sessionId || `session-${index}`}
                          initial={{ x: -20, opacity: 0 }}
                          animate={{ x: 0, opacity: 1 }}
                          exit={{ x: 20, opacity: 0 }}
                          transition={{ delay: index * 0.05 }}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <Button
                            variant={isActive ? "default" : "ghost"}
                            className={`w-full justify-start text-left h-auto py-3 px-3 rounded-xl transition-all ${
                              isActive
                                ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg dark:shadow-blue-500/20"
                                : "hover:bg-gray-100 dark:hover:bg-gray-800/50"
                            }`}
                            onClick={() => {
                              setCurrentSessionId(session.sessionId);
                              setMessages(session.messages || []);
                            }}
                          >
                            <div className="flex flex-col items-start gap-1.5 w-full">
                              <span className="text-sm font-medium truncate w-full">
                                {session.title || "Nueva Conversación"}
                              </span>
                              <div className="flex items-center gap-2 text-xs opacity-80">
                                <Clock className="h-3 w-3" />
                                <span>{date.toLocaleDateString("es-ES")}</span>
                                {session.counters && (
                                  <Badge
                                    variant="secondary"
                                    className={`text-xs px-1.5 py-0 ${
                                      isActive ? "bg-white/20 text-white" : ""
                                    }`}
                                  >
                                    {session.counters.messages}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </Button>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </motion.div>

      {/* Chat Area */}
      <motion.div
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="lg:col-span-3 h-full"
      >
        <Card className="h-full flex flex-col border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg overflow-hidden !p-0">
          <CardHeader className="border-b dark:border-gray-700/50 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{
                    duration: 20,
                    repeat: Infinity,
                    ease: "linear",
                  }}
                >
                  <Sparkles className="h-5 w-5 text-purple-500" />
                </motion.div>
                <CardTitle>Chat AI</CardTitle>
              </div>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger className="w-48 border-2 dark:border-gray-700/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.isArray(models) && models.length > 0 ? (
                    models.map((model, index) => {
                      const modelKey =
                        typeof model === "string" ? model : `model-${index}`;
                      const modelValue =
                        typeof model === "string" ? model : String(model);
                      return (
                        <SelectItem key={modelKey} value={modelValue}>
                          {modelValue}
                        </SelectItem>
                      );
                    })
                  ) : (
                    <SelectItem value="gpt-4o-mini">gpt-4o-mini</SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0">
            {/* Messages */}
            <ScrollArea className="flex-1 p-6" ref={scrollRef}>
              {messages.length === 0 ? (
                <motion.div
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="flex flex-col items-center justify-center h-full text-center text-muted-foreground"
                >
                  <motion.div
                    animate={{
                      y: [0, -10, 0],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  >
                    <Bot className="h-20 w-20 mb-4 opacity-20 dark:opacity-10" />
                  </motion.div>
                  <p className="text-lg font-medium">Inicia una conversación</p>
                  <p className="text-sm mt-1">
                    Envía un mensaje para comenzar a chatear con IA
                  </p>
                </motion.div>
              ) : (
                <div className="space-y-6">
                  <AnimatePresence>
                    {messages.map((msg, idx) => (
                      <motion.div
                        key={msg.id || idx}
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.3 }}
                        className={`flex items-start space-x-3 ${
                          msg.role === "user" ? "justify-end" : "justify-start"
                        }`}
                      >
                        {msg.role === "assistant" && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg"
                          >
                            <Bot className="h-5 w-5 text-white" />
                          </motion.div>
                        )}
                        <motion.div
                          whileHover={{ scale: 1.02 }}
                          className={`max-w-[75%] rounded-2xl p-4 shadow-md ${
                            msg.role === "user"
                              ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white"
                              : "bg-white dark:bg-gray-800 border-2 dark:border-gray-700/50"
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap leading-relaxed">
                            {msg.content}
                          </p>
                        </motion.div>
                        {msg.role === "user" && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center flex-shrink-0 shadow-lg"
                          >
                            <User className="h-5 w-5 text-white" />
                          </motion.div>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {loading && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-start space-x-3"
                    >
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                        <Bot className="h-5 w-5 text-white" />
                      </div>
                      <div className="bg-white dark:bg-gray-800 border-2 dark:border-gray-700/50 rounded-2xl p-4 shadow-md">
                        <div className="flex space-x-2">
                          <motion.div
                            className="w-2.5 h-2.5 bg-blue-500 rounded-full"
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 0.6, repeat: Infinity }}
                          />
                          <motion.div
                            className="w-2.5 h-2.5 bg-purple-500 rounded-full"
                            animate={{ y: [0, -8, 0] }}
                            transition={{
                              duration: 0.6,
                              repeat: Infinity,
                              delay: 0.2,
                            }}
                          />
                          <motion.div
                            className="w-2.5 h-2.5 bg-pink-500 rounded-full"
                            animate={{ y: [0, -8, 0] }}
                            transition={{
                              duration: 0.6,
                              repeat: Infinity,
                              delay: 0.4,
                            }}
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              )}
            </ScrollArea>

            {/* Input */}
            <motion.form
              onSubmit={handleSendMessage}
              className="p-4 border-t dark:border-gray-700/50 bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-gray-800/30 dark:to-gray-800/30"
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex space-x-3">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Escribe tu mensaje aquí..."
                  disabled={loading}
                  className="flex-1 border-2 dark:border-gray-700/50 bg-white dark:bg-gray-900/50 rounded-xl focus:ring-2 focus:ring-purple-500"
                />
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    type="submit"
                    disabled={loading || !message.trim()}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl px-6 shadow-lg"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </motion.div>
              </div>
            </motion.form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
