import axios, { AxiosError } from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refreshToken");
        if (!refreshToken) {
          throw new Error("No refresh token");
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refreshToken,
        });

        const { accessToken } = response.data;
        localStorage.setItem("accessToken", accessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        }

        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: { email: string; password: string; name: string }) =>
    api.post("/auth/register", data),

  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),

  logout: () => api.post("/auth/logout"),

  getProfile: () => api.get("/auth/profile"),
};

// Chat API
export const chatAPI = {
  sendMessage: (data: {
    message: string;
    sessionId?: string;
    model?: string;
  }) => api.post("/chat", data),

  getSessions: () => api.get("/chat/sessions"),

  getSession: (sessionId: string) => api.get(`/chat/sessions/${sessionId}`),

  getModels: () => api.get("/chat/models"),
};

// Image API
export const imageAPI = {
  generate: (data: { prompt: string; model?: string }) =>
    api.post("/image/generate", data),

  getImage: (id: string) => api.get(`/image/${id}`),

  downloadImage: (id: string) =>
    api.get(`/image/${id}/download`, { responseType: "blob" }),
};

// Speech API
export const speechAPI = {
  generate: (data: { prompt: string; voice?: string; language?: string }) =>
    api.post("/speech/generate", data),

  getSpeech: (id: string) => api.get(`/speech/${id}`),

  downloadSpeech: (id: string) =>
    api.get(`/speech/${id}/download`, { responseType: "blob" }),
};

// Analytics API
export const analyticsAPI = {
  getUserStats: () => api.get("/analytics/user/me"),

  getServiceStats: (type: string) => api.get(`/analytics/service/${type}`),

  getSystemStats: () => api.get("/analytics/system"),

  getUsageStats: () => api.get("/analytics/usage"),
};
