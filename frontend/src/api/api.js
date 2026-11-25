import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 120000,
});


export const getHealth = () =>
  api.get("/health");

export const getChromaCount = () =>
  api.get("/chroma-count");

export const getNews = () =>
  api.get("/news");

export const getNewsById = (id) =>
  api.get(`/news/${id}`);

export const fetchNews = () =>
  api.post("/fetch-news");

export const processNews = () =>
  api.post("/process-news");

export const runPipeline = () =>
  api.post("/run-pipeline");

export const getDailyBriefs = () =>
  api.get("/daily-briefs");

export const generateDailyBrief = () =>
  api.post("/generate-daily-brief");

export const previewEmail = () =>
  api.get("/preview-email");

export const sendDailyEmail = () =>
  api.post("/send-daily-email");


export const askNewsAgent = (
  query,
  nResults = 10,
  maxDistance = 1.8
) =>
  api.get("/ask", {
    params: {
      query,
      n_results: nResults,
      max_distance: maxDistance,
    },
  });

export const ragSearch = (
  query,
  nResults = 10,
  maxDistance = 1.8
) =>
  api.get("/rag-search", {
    params: {
      query,
      n_results: nResults,
      max_distance: maxDistance,
    },
  });

export const subscribeUser = (payload) =>
  api.post("/subscribe", payload);

export const getSubscribers = () =>
  api.get("/subscribers");

export const sendToSubscribers = () =>
  api.post("/send-to-subscribers");

export const runDailyJob = () =>
  api.post("/run-daily-job");

export const refreshNews = () =>
  api.post("/refresh-news");

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    }

    return Promise.reject(error);
  }
);

export const registerUser = (data) => {
  return api.post("/auth/register", data);
};

export const loginUser = (data) => {
  return api.post("/auth/login", data);
};

export const getCurrentUser = () => {
  return api.get("/auth/me");
};


export default api;