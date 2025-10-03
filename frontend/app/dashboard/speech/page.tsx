"use client";

import { useState, useEffect } from "react";
import { speechAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import {
  Download,
  Volume2,
  Loader2,
  Mic,
  Play,
  Pause,
  Radio,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface GeneratedSpeech {
  id: string;
  prompt: string;
  status: string;
  s3?: {
    url?: string;
    key?: string;
  };
  meta?: {
    voice?: string;
    language?: string;
  };
  created_at?: string;
}

export default function SpeechPage() {
  const [prompt, setPrompt] = useState("");
  const [language, setLanguage] = useState("es");
  const [speeches, setSpeeches] = useState<GeneratedSpeech[]>([]);
  const [loading, setLoading] = useState(false);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [audioUrls, setAudioUrls] = useState<Record<string, string>>({});
  const [loadingTimes, setLoadingTimes] = useState<Record<string, number>>({});
  const [startTimes, setStartTimes] = useState<Record<string, number>>({});

  // Load history from localStorage on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const savedHistory = localStorage.getItem("speechHistory");
        if (savedHistory) {
          const history = JSON.parse(savedHistory) as Array<{
            id: string;
            prompt: string;
          }>;
          const loadedSpeeches: GeneratedSpeech[] = [];
          const validHistory: Array<{ id: string; prompt: string }> = [];

          // Load speeches from most recent to oldest (reverse the array)
          for (const item of history.slice().reverse()) {
            try {
              const response = await speechAPI.getSpeech(item.id);
              if (response.data) {
                // Ensure prompt is preserved from localStorage if not in response
                const speechData = {
                  ...response.data,
                  prompt: response.data.prompt || item.prompt,
                };
                loadedSpeeches.push(speechData);
                validHistory.push(item);
              }
            } catch (error: any) {
              // If 404, the speech no longer exists - skip it
              if (error.response?.status === 404) {
                console.log(
                  `Speech ${item.id} no longer exists, removing from history`
                );
              } else {
                console.error(`Failed to load speech ${item.id}:`, error);
                // Keep in history for other errors (network issues, etc)
                validHistory.push(item);
              }
            }
          }

          // Update localStorage with only valid IDs
          if (validHistory.length !== history.length) {
            localStorage.setItem(
              "speechHistory",
              JSON.stringify(validHistory.reverse())
            );
          }

          if (loadedSpeeches.length > 0) {
            setSpeeches(loadedSpeeches);
          }
        }
      } catch (error) {
        console.error("Failed to load speech history:", error);
      }
    };

    loadHistory();
  }, []);

  // Load audio blobs when speeches change
  useEffect(() => {
    speeches.forEach((speech) => {
      if (speech.status === "completed" && speech.id && !audioUrls[speech.id]) {
        loadAudioBlob(speech.id);
      }
    });
  }, [speeches]);

  const loadAudioBlob = async (speechId: string) => {
    try {
      const response = await speechAPI.downloadSpeech(speechId);

      // Check if response is JSON with a URL
      if (
        response.data instanceof Blob &&
        response.data.type === "application/json"
      ) {
        const text = await response.data.text();
        const jsonData = JSON.parse(text);

        // If JSON contains a download URL, use it directly
        if (jsonData.download_url) {
          let audioUrl = jsonData.download_url;
          // Replace internal Docker hostname with localhost
          audioUrl = audioUrl.replace(
            "http://minio:9000",
            "http://localhost:9000"
          );
          audioUrl = audioUrl.replace(
            "https://minio:9000",
            "https://localhost:9000"
          );
          setAudioUrls((prev) => ({ ...prev, [speechId]: audioUrl }));
          return;
        }
      }

      // Otherwise treat as audio blob
      const blob = new Blob([response.data], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      setAudioUrls((prev) => ({ ...prev, [speechId]: url }));
    } catch (error) {
      console.error("Failed to load audio blob:", error);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    try {
      setLoading(true);
      console.log("🎤 Generating speech with language:", language);
      const response = await speechAPI.generate({
        prompt: prompt.trim(),
        voice: language, // Backend expects 'voice' parameter, not 'language'
        language: language, // Send both to be safe
      });

      console.log("✅ Speech generated:", response.data);
      const newSpeech = response.data;
      setSpeeches((prev) => [newSpeech, ...prev]);

      // Track start time
      if (newSpeech.id) {
        setStartTimes((prev) => ({ ...prev, [newSpeech.id]: Date.now() }));

        // Save to localStorage with prompt
        const savedHistory = localStorage.getItem("speechHistory");
        const history = savedHistory ? JSON.parse(savedHistory) : [];
        const exists = history.find((item: any) => item.id === newSpeech.id);
        if (!exists) {
          history.push({
            id: newSpeech.id,
            prompt: prompt.trim(),
          });
          localStorage.setItem("speechHistory", JSON.stringify(history));
        }
      }

      setPrompt("");
      toast.success("🎤 Speech generation started!");

      // Poll for completion
      if (newSpeech.id) {
        pollSpeechStatus(newSpeech.id);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to generate speech");
    } finally {
      setLoading(false);
    }
  };

  const pollSpeechStatus = async (speechId: string) => {
    let attempts = 0;
    const maxAttempts = 30; // 1 minute with 2 second intervals

    const poll = async () => {
      try {
        const response = await speechAPI.getSpeech(speechId);
        const updatedSpeech = response.data;

        setSpeeches((prev) =>
          prev.map((speech) =>
            speech.id === speechId ? updatedSpeech : speech
          )
        );

        if (
          updatedSpeech.status === "completed" ||
          updatedSpeech.status === "failed"
        ) {
          if (updatedSpeech.status === "completed") {
            // Calculate loading time
            const startTime = startTimes[speechId];
            if (startTime) {
              const loadTime = ((Date.now() - startTime) / 1000).toFixed(1);
              setLoadingTimes((prev) => ({
                ...prev,
                [speechId]: parseFloat(loadTime),
              }));
              toast.success(`🎵 Speech generated in ${loadTime}s!`);
            } else {
              toast.success("🎵 Speech generated successfully!");
            }
          } else {
            toast.error("❌ Speech generation failed");
          }
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error("Failed to poll speech status:", error);
      }
    };

    poll();
  };

  const handleDownload = async (speech: GeneratedSpeech) => {
    try {
      const response = await speechAPI.downloadSpeech(speech.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `speech-${speech.id}.mp3`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("📥 Audio downloaded!");
    } catch (error) {
      toast.error("Failed to download audio");
    }
  };

  // Format relative time
  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return "";
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now.getTime() - then.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500/10 text-green-600 border-green-500/20";
      case "processing":
      case "pending":
        return "bg-blue-500/10 text-blue-600 border-blue-500/20";
      case "failed":
        return "bg-red-500/10 text-red-600 border-red-500/20";
      default:
        return "bg-gray-500/10 text-gray-600 border-gray-500/20";
    }
  };

  // Get language flag emoji
  const getLanguageFlag = (lang: string) => {
    const flags: Record<string, string> = {
      es: "🇪🇸",
      en: "🇺🇸",
      fr: "🇫🇷",
      de: "🇩🇪",
      it: "🇮🇹",
      pt: "🇵🇹",
      zh: "🇨🇳",
      ja: "🇯🇵",
      ko: "🇰🇷",
      ru: "🇷🇺",
    };
    return flags[lang] || "🌐";
  };

  return (
    <div className="space-y-6">
      {/* Generation Form */}
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg !p-0">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 border-b dark:border-gray-700/50 py-4">
            <CardTitle className="flex items-center space-x-2">
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                <Radio className="h-5 w-5 text-purple-500" />
              </motion.div>
              <span>Text to Speech</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            <div className="space-y-2">
              <Label htmlFor="language" className="flex items-center space-x-2">
                <Volume2 className="h-4 w-4 text-purple-500" />
                <span>Idioma / Language</span>
              </Label>
              <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger className="border-2 dark:border-gray-700/50 bg-white dark:bg-gray-900/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="es">🇪🇸 Español</SelectItem>
                  <SelectItem value="en">🇺🇸 English</SelectItem>
                  <SelectItem value="fr">🇫🇷 Français</SelectItem>
                  <SelectItem value="de">🇩🇪 Deutsch</SelectItem>
                  <SelectItem value="it">🇮🇹 Italiano</SelectItem>
                  <SelectItem value="pt">🇵🇹 Português</SelectItem>
                  <SelectItem value="zh">🇨🇳 中文</SelectItem>
                  <SelectItem value="ja">🇯🇵 日本語</SelectItem>
                  <SelectItem value="ko">🇰🇷 한국어</SelectItem>
                  <SelectItem value="ru">🇷🇺 Русский</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="prompt" className="flex items-center space-x-2">
                <Mic className="h-4 w-4 text-purple-500" />
                <span>Texto / Text</span>
              </Label>
              <Textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter the text you want to convert to speech..."
                disabled={loading}
                rows={6}
                className="resize-none border-2 dark:border-gray-700/50 bg-white dark:bg-gray-900/50 focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating
                  </>
                ) : (
                  <>
                    <Volume2 className="mr-2 h-4 w-4" />
                    Generate Speech
                  </>
                )}
              </Button>
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Generated Speeches */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center space-x-2 mb-4">
          <Volume2 className="h-6 w-6 text-purple-500" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
            Your Audio Files
          </h2>
        </div>
        {speeches.length === 0 ? (
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
          >
            <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm !p-0">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                >
                  <Volume2 className="h-20 w-20 mb-4 opacity-20 dark:opacity-10" />
                </motion.div>
                <p className="text-lg font-medium">No audio files yet</p>
                <p className="text-sm mt-1">
                  Generate your first text-to-speech above
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <div className="space-y-4">
            <AnimatePresence>
              {speeches.map((speech, index) => (
                <motion.div
                  key={speech.id}
                  initial={{ opacity: 0, x: -50 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 50 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge
                              className={`border-2 shadow-lg ${getStatusColor(
                                speech.status
                              )}`}
                            >
                              {speech.status === "completed" && "✓ "}
                              {speech.status === "processing" && "⚡ "}
                              {speech.status === "pending" && "⏳ "}
                              {speech.status === "failed" && "✗ "}
                              {speech.status}
                            </Badge>
                            {speech.meta?.voice && (
                              <Badge variant="outline" className="border-2">
                                {getLanguageFlag(speech.meta.voice)}{" "}
                                {speech.meta.voice.toUpperCase()}
                              </Badge>
                            )}
                            {loadingTimes[speech.id] && (
                              <Badge className="bg-purple-500/10 text-purple-600 border-purple-500/20 border-2">
                                ⚡ {loadingTimes[speech.id]}s
                              </Badge>
                            )}
                            {speech.created_at && (
                              <span className="text-xs text-muted-foreground">
                                🕐 {formatRelativeTime(speech.created_at)}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {speech.prompt}
                          </p>
                        </div>
                      </div>

                      {speech.status === "completed" && (
                        <motion.div
                          className="space-y-3"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                        >
                          {audioUrls[speech.id] ? (
                            <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 rounded-lg">
                              <audio
                                controls
                                className="w-full"
                                src={audioUrls[speech.id]}
                                onPlay={() => setPlayingId(speech.id)}
                                onPause={() => setPlayingId(null)}
                              >
                                Your browser does not support the audio element.
                              </audio>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center py-4">
                              <motion.div
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                              >
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => loadAudioBlob(speech.id)}
                                  className="border-2 dark:border-gray-700/50"
                                >
                                  <Volume2 className="mr-2 h-4 w-4" />
                                  Load Audio
                                </Button>
                              </motion.div>
                            </div>
                          )}
                          <motion.div
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <Button
                              size="sm"
                              variant="outline"
                              className="w-full border-2 dark:border-gray-700/50 bg-white dark:bg-gray-900/50"
                              onClick={() => handleDownload(speech)}
                            >
                              <Download className="mr-2 h-4 w-4" />
                              Download Audio
                            </Button>
                          </motion.div>
                        </motion.div>
                      )}

                      {(speech.status === "processing" ||
                        speech.status === "pending") && (
                        <div className="flex items-center justify-center py-8">
                          <div className="text-center space-y-3">
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{
                                duration: 2,
                                repeat: Infinity,
                                ease: "linear",
                              }}
                            >
                              <Loader2 className="h-12 w-12 mx-auto text-purple-500" />
                            </motion.div>
                            <div>
                              <p className="text-sm font-medium text-purple-600 dark:text-purple-400">
                                🎵 Generating audio...
                              </p>
                              {startTimes[speech.id] && (
                                <motion.p
                                  className="text-xs text-muted-foreground mt-1"
                                  key={Math.floor(Date.now() / 1000)}
                                  initial={{ opacity: 0 }}
                                  animate={{ opacity: 1 }}
                                >
                                  {Math.floor(
                                    (Date.now() - startTimes[speech.id]) / 1000
                                  )}
                                  s elapsed
                                </motion.p>
                              )}
                            </div>
                            {/* Progress bar */}
                            <div className="w-full max-w-xs mx-auto">
                              <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <motion.div
                                  className="h-full bg-gradient-to-r from-blue-500 to-purple-600"
                                  initial={{ width: "0%" }}
                                  animate={{ width: "100%" }}
                                  transition={{
                                    duration: 30,
                                    repeat: Infinity,
                                    ease: "linear",
                                  }}
                                />
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {speech.status === "failed" && (
                        <motion.div
                          className="bg-red-500/10 text-red-500 dark:text-red-400 text-sm p-3 rounded-md text-center border-2 border-red-500/20"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                        >
                          Generation failed. Please try again.
                        </motion.div>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </motion.div>
    </div>
  );
}
