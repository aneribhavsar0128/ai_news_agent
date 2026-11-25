import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";

import { AuthProvider, useAuth } from "./context/AuthContext";

import AskAI from "./pages/AskAI";
import Briefs from "./pages/Briefs";
import Login from "./pages/Login";
import News from "./pages/News";
import Register from "./pages/Register";
import Subscribe from "./pages/Subscribe";


function HomeRedirect() {
  const {
    isAuthenticated,
    loading,
  } = useAuth();

  if (loading) {
    return (
      <div className="page-loading">
        Checking authentication...
      </div>
    );
  }

  return (
    <Navigate
      to={isAuthenticated ? "/news" : "/login"}
      replace
    />
  );
}


function PublicOnlyRoute({ children }) {
  const {
    isAuthenticated,
    loading,
  } = useAuth();

  if (loading) {
    return (
      <div className="page-loading">
        Checking authentication...
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to="/news"
        replace
      />
    );
  }

  return children;
}


function AppContent({
  theme,
  onToggleTheme,
}) {
  return (
    <div className="app-shell">
      <Navbar
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <main className="main-content">
        <Routes>
          {/* Automatic redirect */}
          <Route
            path="/"
            element={<HomeRedirect />}
          />

          {/* Public authentication routes */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />

          <Route
            path="/register"
            element={
              <PublicOnlyRoute>
                <Register />
              </PublicOnlyRoute>
            }
          />

          {/* Public newsletter subscription page */}
          <Route
            path="/subscribe"
            element={<Subscribe />}
          />

          {/* Protected AI chat */}
          <Route
            path="/ask"
            element={
              <ProtectedRoute>
                <AskAI />
              </ProtectedRoute>
            }
          />

          {/* Protected news page */}
          <Route
            path="/news"
            element={
              <ProtectedRoute>
                <News />
              </ProtectedRoute>
            }
          />

          {/* Protected briefs page */}
          <Route
            path="/briefs"
            element={
              <ProtectedRoute>
                <Briefs />
              </ProtectedRoute>
            }
          />

          {/* Unknown route */}
          <Route
            path="*"
            element={<HomeRedirect />}
          />
        </Routes>
      </main>
    </div>
  );
}


function App() {
  const [theme, setTheme] = useState(() => {
    return (
      localStorage.getItem(
        "news-agent-theme"
      ) || "dark"
    );
  });

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      theme
    );

    localStorage.setItem(
      "news-agent-theme",
      theme
    );
  }, [theme]);

  const toggleTheme = () => {
    setTheme((currentTheme) =>
      currentTheme === "dark"
        ? "light"
        : "dark"
    );
  };

  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent
          theme={theme}
          onToggleTheme={toggleTheme}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;