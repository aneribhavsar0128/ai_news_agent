import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [submitting, setSubmitting] =
    useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSubmitting(true);

    try {
      await login(
        formData.email,
        formData.password
      );

      const destination =
        location.state?.from?.pathname ||
        "/news";

      navigate(destination, {
        replace: true,
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Invalid email or password."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="news-auth-page">
      <div className="news-auth-layout">
        <div className="news-auth-card">
          <div className="news-auth-card-header">
            <img src={logo} alt="News Agent Logo" className="news-auth-logo-img" />
            <h2>Login</h2>
          </div>

          <p className="news-auth-card-text">
            Enter your registered email and
            password to continue.
          </p>

          {location.state?.message && (
            <div className="news-auth-alert success">
              {location.state.message}
            </div>
          )}

          {error && (
            <div className="news-auth-alert error">
              {error}
            </div>
          )}

          <form
            className="news-auth-form"
            onSubmit={handleSubmit}
          >
            <div className="news-auth-field">
              <label htmlFor="email">
                Email address
              </label>

              <div className="news-auth-input-wrapper">
                <span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                </span>

                <input
                  id="email"
                  type="email"
                  name="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="news-auth-field">
              <label htmlFor="password">
                Password
              </label>

              <div className="news-auth-input-wrapper">
                <span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </span>

                <input
                  id="password"
                  type="password"
                  name="password"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              className="news-auth-primary-button"
              disabled={submitting}
            >
              {submitting
                ? "Logging in..."
                : "Login to News Agent"}
            </button>
          </form>

          <div className="news-auth-divider">
            <span>
              New to News Agent?
            </span>
          </div>

          <Link
            to="/register"
            className="news-auth-secondary-button"
          >
            Create an account
          </Link>

          <p className="news-auth-footer">
            Your password is securely hashed and
            never stored as plain text.
          </p>
        </div>
      </div>
    </section>
  );
}

export default Login;