"use client";

import { useState, useEffect } from "react";
import { analyticsAPI } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart3,
  TrendingUp,
  Activity,
  Clock,
  Zap,
  Users,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface UserStats {
  total_requests: number;
  services_used: (string | any)[]; // Can be string or object
  last_activity?: string;
}

interface ServiceStats {
  total_requests: number;
  unique_users: number;
  avg_response_time?: number;
  avg_response_time_ms?: number; // Backend might use this field
}

interface SystemStats {
  total_requests: number;
  total_users: number;
  services: {
    [key: string]: number | any; // Can be number or object
  };
}

interface UsageStats {
  daily: Array<{
    date: string;
    count: number;
  }>;
  by_service: {
    [key: string]: number;
  };
}

export default function AnalyticsPage() {
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [serviceStats, setServiceStats] = useState<{
    [key: string]: ServiceStats;
  }>({});
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState("chat");

  // Backend to Frontend service name mapping
  const backendToFrontend: { [key: string]: string } = {
    llm_chat: "chat",
    text_to_image: "image",
    text_to_speech: "speech",
  };

  // Frontend to Backend service name mapping
  const frontendToBackend: { [key: string]: string } = {
    chat: "llm_chat",
    image: "text_to_image",
    speech: "text_to_speech",
  };

  // Display names for services
  const serviceDisplayNames: { [key: string]: string } = {
    llm_chat: "Chat",
    text_to_image: "Image Generation",
    text_to_speech: "Text to Speech",
    chat: "Chat",
    image: "Image Generation",
    speech: "Text to Speech",
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);

    // Note: Analytics service is optional. If not running, the page will show zeros.
    const results = await Promise.allSettled([
      analyticsAPI
        .getUserStats()
        .catch(() => ({ data: { total_requests: 0, services_used: [] } })),
      analyticsAPI.getSystemStats().catch(() => ({
        data: { total_requests: 0, total_users: 0, services: {} },
      })),
      analyticsAPI
        .getUsageStats()
        .catch(() => ({ data: { daily: [], by_service: {} } })),
    ]);

    // Handle user stats
    if (results[0].status === "fulfilled") {
      setUserStats(results[0].value.data);
    }

    // Handle system stats
    if (results[1].status === "fulfilled") {
      setSystemStats(results[1].value.data);
    }

    // Handle usage stats
    if (results[2].status === "fulfilled") {
      setUsageStats(results[2].value.data);
    }

    // Load service stats for each service (optional - requires analytics service)
    const services = ["chat", "image", "speech"];
    const serviceStatsData: { [key: string]: ServiceStats } = {};

    const serviceResults = await Promise.allSettled(
      services.map((service) =>
        analyticsAPI.getServiceStats(frontendToBackend[service]).catch(() => ({
          data: { total_requests: 0, unique_users: 0 },
        }))
      )
    );

    serviceResults.forEach((result, index) => {
      if (result.status === "fulfilled") {
        serviceStatsData[services[index]] = result.value.data;
      }
    });

    setServiceStats(serviceStatsData);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-8 w-8 text-purple-500" />
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
            Analytics
          </h1>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm">
                <CardHeader>
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.div
        className="flex items-center justify-between"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center space-x-2">
          <motion.div
            animate={{ rotate: [0, 360] }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          >
            <BarChart3 className="h-8 w-8 text-purple-500" />
          </motion.div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
            Analytics
          </h1>
        </div>
        <Badge variant="outline" className="border-2 dark:border-gray-700/50">
          Last 30 days
        </Badge>
      </motion.div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Requests
              </CardTitle>
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                <Activity className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <motion.div
                className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                {userStats?.total_requests || 0}
              </motion.div>
              <p className="text-xs text-muted-foreground mt-1">
                Your total API requests
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Services Used
              </CardTitle>
              <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg">
                <TrendingUp className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <motion.div
                className="text-2xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 dark:from-green-400 dark:to-emerald-400 bg-clip-text text-transparent"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
              >
                {userStats?.services_used?.length || 0}
              </motion.div>
              <p className="text-xs text-muted-foreground mt-1">
                Active services
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                System Requests
              </CardTitle>
              <div className="p-2 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg">
                <Zap className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <motion.div
                className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-red-600 dark:from-orange-400 dark:to-red-400 bg-clip-text text-transparent"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                {systemStats?.total_requests || 0}
              </motion.div>
              <p className="text-xs text-muted-foreground mt-1">
                Total platform requests
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Total Users</CardTitle>
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg">
                <Users className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <motion.div
                className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 dark:from-purple-400 dark:to-pink-400 bg-clip-text text-transparent"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
              >
                {systemStats?.total_users || 0}
              </motion.div>
              <p className="text-xs text-muted-foreground mt-1">
                Platform users
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Service Statistics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg !p-0">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 border-b dark:border-gray-700/50 py-4">
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5 text-purple-500" />
              <span>Service Statistics</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <Tabs defaultValue="chat">
              <TabsList className="grid w-full grid-cols-3 bg-gray-100 dark:bg-gray-800/50 p-1">
                <TabsTrigger
                  value="chat"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 data-[state=active]:text-white"
                >
                  Chat
                </TabsTrigger>
                <TabsTrigger
                  value="image"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 data-[state=active]:text-white"
                >
                  Image
                </TabsTrigger>
                <TabsTrigger
                  value="speech"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-purple-600 data-[state=active]:text-white"
                >
                  Speech
                </TabsTrigger>
              </TabsList>

              {["chat", "image", "speech"].map((service) => (
                <TabsContent
                  key={service}
                  value={service}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 }}
                    >
                      <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-800/50">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium text-muted-foreground">
                            Total Requests
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {serviceStats[service]?.total_requests || 0}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.2 }}
                    >
                      <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-800/50">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium text-muted-foreground">
                            Unique Users
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                            {serviceStats[service]?.unique_users || 0}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 }}
                    >
                      <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-800/50">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium text-muted-foreground">
                            Avg Response Time
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {serviceStats[service]?.avg_response_time ||
                            serviceStats[service]?.avg_response_time_ms
                              ? `${(
                                  serviceStats[service]?.avg_response_time ||
                                  serviceStats[service]?.avg_response_time_ms ||
                                  0
                                ).toFixed(0)}ms`
                              : "N/A"}
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>

      {/* Usage by Service */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg !p-0">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 border-b dark:border-gray-700/50 py-4">
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5 text-purple-500" />
                <span>Your Service Usage</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                <AnimatePresence>
                  {userStats?.services_used?.map((service, index) => {
                    // Get the backend service name
                    const backendServiceName =
                      typeof service === "string"
                        ? service
                        : (service as any).service_type || `service-${index}`;

                    // Get the display name
                    const displayName =
                      serviceDisplayNames[backendServiceName] ||
                      backendServiceName;

                    // Get request count - try both backend and frontend names
                    const requestCount =
                      usageStats?.by_service?.[backendServiceName] ||
                      usageStats?.by_service?.[
                        backendToFrontend[backendServiceName]
                      ] ||
                      0;

                    return (
                      <motion.div
                        key={backendServiceName}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-center justify-between p-3 rounded-lg bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-gray-800/30 dark:to-gray-800/30"
                      >
                        <div className="flex items-center space-x-3">
                          <motion.div
                            className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg"
                            whileHover={{ scale: 1.1, rotate: 5 }}
                          >
                            <span className="text-white text-sm font-bold">
                              {displayName[0].toUpperCase()}
                            </span>
                          </motion.div>
                          <span className="font-medium">{displayName}</span>
                        </div>
                        <Badge className="bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg">
                          {requestCount} requests
                        </Badge>
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
                {(!userStats?.services_used ||
                  userStats.services_used.length === 0) && (
                  <motion.p
                    className="text-center text-muted-foreground py-8"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    No service usage data yet
                  </motion.p>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg !p-0">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 border-b dark:border-gray-700/50 py-4">
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="h-5 w-5 text-purple-500" />
                <span>System Distribution</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                {systemStats?.services &&
                  Object.entries(systemStats.services).map(
                    ([service, count], index) => {
                      const requestCount =
                        typeof count === "number"
                          ? count
                          : (count as any).total_requests || 0;

                      const displayName =
                        serviceDisplayNames[service] || service;

                      return (
                        <motion.div
                          key={service}
                          className="space-y-2"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">
                              {displayName}
                            </span>
                            <span className="text-sm text-muted-foreground">
                              {requestCount} requests
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2 overflow-hidden">
                            <motion.div
                              className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                              initial={{ width: 0 }}
                              animate={{
                                width: `${
                                  systemStats.total_requests
                                    ? (requestCount /
                                        systemStats.total_requests) *
                                      100
                                    : 0
                                }%`,
                              }}
                              transition={{
                                duration: 1,
                                delay: index * 0.1 + 0.5,
                              }}
                            />
                          </div>
                        </motion.div>
                      );
                    }
                  )}
                {(!systemStats?.services ||
                  Object.keys(systemStats.services).length === 0) && (
                  <motion.p
                    className="text-center text-muted-foreground py-8"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    No system data yet
                  </motion.p>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Daily Usage Trend */}
      {usageStats?.daily && usageStats.daily.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Card className="border-2 dark:border-gray-700/50 dark:bg-gray-900/50 backdrop-blur-sm shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-gray-800/50 dark:to-gray-800/30 border-b dark:border-gray-700/50">
              <CardTitle className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-purple-500" />
                <span>Daily Usage Trend</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-3">
                {usageStats.daily.slice(-7).map((day, index) => (
                  <motion.div
                    key={day.date}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/50 dark:hover:from-gray-800/30 dark:hover:to-gray-800/30 transition-colors"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <span className="text-sm font-medium text-muted-foreground min-w-[120px]">
                      {new Date(day.date).toLocaleDateString()}
                    </span>
                    <div className="flex items-center space-x-3 flex-1">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-800 h-2 rounded-full overflow-hidden">
                        <motion.div
                          className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                          initial={{ width: 0 }}
                          animate={{
                            width: `${Math.min(day.count * 10, 100)}%`,
                          }}
                          transition={{ duration: 1, delay: index * 0.1 + 0.3 }}
                        />
                      </div>
                      <span className="text-sm font-bold w-12 text-right bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
                        {day.count}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
