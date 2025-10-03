"use client";

import { useState, useEffect } from "react";
import { imageAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  Download,
  Image as ImageIcon,
  Loader2,
  Sparkles,
  Wand2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface GeneratedImage {
  id: string;
  prompt?: string;
  status: string;
  s3Keys?: {
    image?: string;
  };
  meta?: {
    model?: string;
    params?: {
      prompt?: string;
    };
  };
  created_at?: string;
}

export default function ImagesPage() {
  const [prompt, setPrompt] = useState("");
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<GeneratedImage | null>(
    null
  );
  const [imageUrls, setImageUrls] = useState<Record<string, string>>({});
  const [loadingTimes, setLoadingTimes] = useState<Record<string, number>>({});
  const [startTimes, setStartTimes] = useState<Record<string, number>>({});

  // Load history from localStorage on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const savedHistory = localStorage.getItem("imageHistory");
        if (savedHistory) {
          const history = JSON.parse(savedHistory) as Array<{
            id: string;
            prompt: string;
          }>;
          const loadedImages: GeneratedImage[] = [];
          const validHistory: Array<{ id: string; prompt: string }> = [];

          // Load images from most recent to oldest (reverse the array)
          for (const item of history.slice().reverse()) {
            try {
              const response = await imageAPI.getImage(item.id);
              if (response.data) {
                // Ensure prompt is preserved from localStorage if not in response
                const imageData = {
                  ...response.data,
                  prompt: response.data.prompt || item.prompt,
                };
                loadedImages.push(imageData);
                validHistory.push(item);
              }
            } catch (error: any) {
              // If 404, the image no longer exists - skip it
              if (error.response?.status === 404) {
                console.log(
                  `Image ${item.id} no longer exists, removing from history`
                );
              } else {
                console.error(`Failed to load image ${item.id}:`, error);
                // Keep in history for other errors (network issues, etc)
                validHistory.push(item);
              }
            }
          }

          // Update localStorage with only valid IDs
          if (validHistory.length !== history.length) {
            localStorage.setItem(
              "imageHistory",
              JSON.stringify(validHistory.reverse())
            );
          }

          if (loadedImages.length > 0) {
            setImages(loadedImages);
          }
        }
      } catch (error) {
        console.error("Failed to load image history:", error);
      }
    };

    loadHistory();
  }, []);

  // Load blobs for completed images when images change
  useEffect(() => {
    images.forEach((image) => {
      if (
        image.status === "completed" &&
        image.s3Keys?.image &&
        !imageUrls[image.id]
      ) {
        console.log("Loading blob for image:", image.id);
        loadImageBlob(image.id);
      }
    });
  }, [images]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || loading) return;

    setLoading(true);
    try {
      const response = await imageAPI.generate({
        prompt: prompt.trim(),
        model: "dall-e-3",
      });

      const newImage = response.data;
      console.log("New image created:", newImage);
      setImages((prev) => [newImage, ...prev]);

      // Track start time
      if (newImage.id) {
        setStartTimes((prev) => ({ ...prev, [newImage.id]: Date.now() }));

        // Save to localStorage with prompt
        const savedHistory = localStorage.getItem("imageHistory");
        const history = savedHistory ? JSON.parse(savedHistory) : [];
        const exists = history.find((item: any) => item.id === newImage.id);
        if (!exists) {
          history.push({
            id: newImage.id,
            prompt: prompt.trim(),
          });
          localStorage.setItem("imageHistory", JSON.stringify(history));
        }
      }

      setPrompt("");
      toast.success("🎨 Image generation started!");

      // Poll for completion
      if (newImage.id) {
        pollImageStatus(newImage.id);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.message || "Failed to generate image");
    } finally {
      setLoading(false);
    }
  };

  const loadImageBlob = async (imageId: string) => {
    try {
      console.log("Downloading image:", imageId);
      const response = await imageAPI.downloadImage(imageId);
      console.log("Download response:", response);
      console.log("Response data type:", typeof response.data);

      // Check if response is JSON instead of image
      if (
        response.data instanceof Blob &&
        response.data.type === "application/json"
      ) {
        console.log("Response is JSON, reading it...");
        const text = await response.data.text();
        console.log("JSON content:", text);
        const jsonData = JSON.parse(text);
        console.log("Parsed JSON:", jsonData);

        // If JSON contains a URL, use it directly
        if (jsonData.url || jsonData.signedUrl || jsonData.downloadUrl) {
          let imageUrl =
            jsonData.url || jsonData.signedUrl || jsonData.downloadUrl;
          console.log("Original URL from JSON:", imageUrl);

          // Replace internal Docker hostname with localhost
          imageUrl = imageUrl.replace(
            "http://minio:9000",
            "http://localhost:9000"
          );
          imageUrl = imageUrl.replace(
            "https://minio:9000",
            "https://localhost:9000"
          );

          console.log("Fixed URL for browser:", imageUrl);
          setImageUrls((prev) => ({ ...prev, [imageId]: imageUrl }));
          return imageUrl;
        }
      }

      console.log("Response data:", response.data);
      const blob = new Blob([response.data], { type: "image/png" });
      console.log("Blob created:", blob.size, "bytes");

      const url = URL.createObjectURL(blob);
      console.log("Object URL created:", url);

      setImageUrls((prev) => {
        const newUrls = { ...prev, [imageId]: url };
        console.log("Updated imageUrls:", newUrls);
        return newUrls;
      });
      return url;
    } catch (error) {
      console.error("Failed to load image blob:", error);
      return null;
    }
  };

  const pollImageStatus = async (imageId: string) => {
    let attempts = 0;
    const maxAttempts = 60; // 2 minutes with 2 second intervals

    const poll = async () => {
      try {
        const response = await imageAPI.getImage(imageId);
        const updatedImage = response.data;

        console.log("Poll response for image:", imageId);
        console.log("Updated image data:", updatedImage);
        console.log("Image status:", updatedImage.status);
        console.log("Image S3 data:", updatedImage.s3);

        setImages((prev) =>
          prev.map((img) => {
            if (img.id === imageId) {
              // Preserve the original prompt if it exists
              return {
                ...updatedImage,
                prompt:
                  img.prompt ||
                  updatedImage.prompt ||
                  updatedImage.meta?.params?.prompt,
              };
            }
            return img;
          })
        );

        if (
          updatedImage.status === "completed" ||
          updatedImage.status === "failed"
        ) {
          if (updatedImage.status === "completed") {
            console.log("Image completed! S3 Key:", updatedImage.s3Keys?.image);

            // Calculate loading time
            const startTime = startTimes[imageId];
            if (startTime) {
              const loadTime = ((Date.now() - startTime) / 1000).toFixed(1);
              setLoadingTimes((prev) => ({
                ...prev,
                [imageId]: parseFloat(loadTime),
              }));
              toast.success(`✨ Image generated in ${loadTime}s!`);
            } else {
              toast.success("✨ Image generated successfully!");
            }

            // Load the image as a blob
            await loadImageBlob(imageId);
          } else {
            toast.error("❌ Image generation failed");
          }
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error("Failed to poll image status:", error);
      }
    };

    poll();
  };

  const handleDownload = async (image: GeneratedImage) => {
    try {
      const response = await imageAPI.downloadImage(image.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `image-${image.id}.png`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("📥 Image downloaded!");
    } catch (error) {
      toast.error("Failed to download image");
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
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              >
                <Wand2 className="h-5 w-5 text-purple-500" />
              </motion.div>
              <span>Generate Image</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <form onSubmit={handleGenerate} className="space-y-4">
              <div className="flex space-x-3">
                <Input
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Describe the image you want to generate..."
                  disabled={loading}
                  className="flex-1 border-2 dark:border-gray-700/50 bg-white dark:bg-gray-900/50 rounded-xl focus:ring-2 focus:ring-purple-500"
                />
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    type="submit"
                    disabled={loading || !prompt.trim()}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl px-6 shadow-lg"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate
                      </>
                    )}
                  </Button>
                </motion.div>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* Images Gallery */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center space-x-2 mb-4">
          <Sparkles className="h-6 w-6 text-purple-500" />
          <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
            Your Images
          </h2>
        </div>
        {images.length === 0 ? (
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
          >
            <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm !p-0">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
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
                  <ImageIcon className="h-20 w-20 mb-4 opacity-20 dark:opacity-10" />
                </motion.div>
                <p className="text-lg font-medium">No images yet</p>
                <p className="text-sm mt-1">
                  Generate your first AI image above
                </p>
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatePresence>
              {images.map((image, index) => (
                <motion.div
                  key={image.id}
                  initial={{ opacity: 0, scale: 0.8, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                >
                  <Card className="overflow-hidden border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
                    <CardContent className="p-0">
                      <motion.div
                        className="aspect-square bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 relative"
                        whileHover={{ scale: 1.02 }}
                        transition={{ duration: 0.2 }}
                      >
                        {image.status === "completed" && imageUrls[image.id] ? (
                          <img
                            src={imageUrls[image.id]}
                            alt={
                              image.prompt ||
                              image.meta?.params?.prompt ||
                              "Generated image"
                            }
                            className="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
                            onClick={() => setSelectedImage(image)}
                          />
                        ) : image.status === "completed" &&
                          image.s3Keys?.image &&
                          !imageUrls[image.id] ? (
                          <div className="flex items-center justify-center h-full">
                            <motion.div
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                            >
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => loadImageBlob(image.id)}
                                className="border-2 dark:border-gray-700/50"
                              >
                                <Download className="mr-2 h-4 w-4" />
                                Load Image
                              </Button>
                            </motion.div>
                          </div>
                        ) : image.status === "processing" ||
                          image.status === "pending" ? (
                          <div className="flex items-center justify-center h-full">
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
                                  ✨ Generating...
                                </p>
                                {startTimes[image.id] && (
                                  <motion.p
                                    className="text-xs text-muted-foreground mt-1"
                                    key={Math.floor(Date.now() / 1000)}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                  >
                                    {Math.floor(
                                      (Date.now() - startTimes[image.id]) / 1000
                                    )}
                                    s elapsed
                                  </motion.p>
                                )}
                              </div>
                              {/* Progress bar */}
                              <div className="w-48 mx-auto">
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
                        ) : (
                          <div className="flex items-center justify-center h-full">
                            <div className="text-center text-muted-foreground">
                              <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
                              <p className="text-sm">{image.status}</p>
                            </div>
                          </div>
                        )}
                        <div className="absolute top-2 right-2 flex gap-2">
                          <Badge
                            className={`border-2 shadow-lg ${getStatusColor(
                              image.status
                            )}`}
                          >
                            {image.status === "completed" && "✓ "}
                            {image.status === "processing" && "⚡ "}
                            {image.status === "pending" && "⏳ "}
                            {image.status === "failed" && "✗ "}
                            {image.status}
                          </Badge>
                        </div>
                        {loadingTimes[image.id] && (
                          <div className="absolute bottom-2 left-2">
                            <Badge className="bg-black/60 text-white border-0 shadow-lg">
                              ⚡ {loadingTimes[image.id]}s
                            </Badge>
                          </div>
                        )}
                      </motion.div>
                    </CardContent>
                    <CardFooter className="flex flex-col items-start p-4 space-y-3 bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-gray-800/30 dark:to-gray-800/30">
                      <div className="w-full space-y-2">
                        <p className="text-sm line-clamp-2 font-medium">
                          {image.prompt ||
                            image.meta?.params?.prompt ||
                            "Generated image"}
                        </p>
                        {image.created_at && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              🕐 {formatRelativeTime(image.created_at)}
                            </span>
                            {image.meta?.model && (
                              <>
                                <span>•</span>
                                <span className="flex items-center gap-1">
                                  🎨 {image.meta.model}
                                </span>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                      {image.status === "completed" && (
                        <motion.div
                          className="w-full"
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <Button
                            size="sm"
                            variant="outline"
                            className="w-full border-2 dark:border-gray-700/50 bg-white dark:bg-gray-900/50"
                            onClick={() => handleDownload(image)}
                          >
                            <Download className="mr-2 h-4 w-4" />
                            Download
                          </Button>
                        </motion.div>
                      )}
                    </CardFooter>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </motion.div>

      {/* Image Preview Dialog */}
      <Dialog
        open={!!selectedImage}
        onOpenChange={() => setSelectedImage(null)}
      >
        <DialogContent className="max-w-4xl border-2 dark:border-gray-700/50 dark:bg-gray-900/95 backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              <span>Image Preview</span>
            </DialogTitle>
          </DialogHeader>
          {selectedImage && (
            <div className="space-y-4">
              {imageUrls[selectedImage.id] ? (
                <motion.img
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  src={imageUrls[selectedImage.id]}
                  alt={
                    selectedImage.prompt ||
                    selectedImage.meta?.params?.prompt ||
                    "Generated image"
                  }
                  className="w-full rounded-lg shadow-lg"
                />
              ) : (
                <div className="flex items-center justify-center h-64">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                  >
                    <Loader2 className="h-12 w-12 text-purple-500" />
                  </motion.div>
                </div>
              )}
              <div className="space-y-2 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 rounded-lg">
                <p className="text-sm font-medium">Prompt:</p>
                <p className="text-sm text-muted-foreground">
                  {selectedImage.prompt ||
                    selectedImage.meta?.params?.prompt ||
                    "No prompt available"}
                </p>
              </div>
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Button
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg"
                  onClick={() => selectedImage && handleDownload(selectedImage)}
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Image
                </Button>
              </motion.div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
