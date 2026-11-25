import { useState } from "react";
import {
  Link,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import logo from "../assets/logo.png";

function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    subscribe_to_newsletter: true,
  });

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [error, setError] = useState("");
  const [submitting, setSubmitting] =
    useState(false);

  const handleChange = (event) => {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setFormData((current) => ({
      ...current,
      [name]:
        type === "checkbox"
          ? checked
          : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (
      formData.password !== confirmPassword
    ) {
      setError("Passwords do not match.");
      return;
    }

    if (formData.password.length < 8) {
      setError(
        "Password must contain at least 8 characters."
      );
      return;
    }

    setSubmitting(true);

    try {
      await register(formData);

      navigate("/login", {
        replace: true,
        state: {
          message:
            "Account created successfully. Please login.",
        },
      });
    } catch (err) {
      const detail =
        err.response?.data?.detail;

      if (Array.isArray(detail)) {
        setError(
          detail
            .map((item) => item.msg)
            .join(", ")
        );
      } else {
        setError(
          detail ||
            "Unable to create account."
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="news-auth-page">
      <div className="news-auth-layout register-layout">
        <div className="news-auth-card register-card">
          <div className="news-auth-card-header">
            <img src={logo} alt="News Agent Logo" className="news-auth-logo-img" />
            <h2>Create your account</h2>
          </div>

          <p className="news-auth-card-text">
            Register to access the complete AI
            News Agent platform.
          </p>

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
              <label htmlFor="name">
                Full name
              </label>

              <div className="news-auth-input-wrapper">
                <span>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </span>

                <input
                  id="name"
                  type="text"
                  name="name"
                  placeholder="Enter your full name"
                  value={formData.name}
                  onChange={handleChange}
                  autoComplete="name"
                  required
                />
              </div>
            </div>

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

            <div className="news-auth-password-grid">
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
                    placeholder="Minimum 8 characters"
                    value={formData.password}
                    onChange={handleChange}
                    minLength={8}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </div>

              <div className="news-auth-field">
                <label htmlFor="confirmPassword">
                  Confirm password
                </label>

                <div className="news-auth-input-wrapper">
                  <span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
                  </span>

                  <input
                    id="confirmPassword"
                    type="password"
                    placeholder="Repeat password"
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(
                        event.target.value
                      )
                    }
                    minLength={8}
                    autoComplete="new-password"
                    required
                  />
                </div>
              </div>
            </div>

            <label className="news-auth-checkbox">
              <input
                type="checkbox"
                name="subscribe_to_newsletter"
                checked={
                  formData.subscribe_to_newsletter
                }
                onChange={handleChange}
              />

              <span>
                Subscribe me to the daily
                AI-generated news brief.
              </span>
            </label>

            <button
              type="submit"
              className="news-auth-primary-button"
              disabled={submitting}
            >
              {submitting
                ? "Creating account..."
                : "Create News Agent Account"}
            </button>
          </form>

          <div className="news-auth-divider">
            <span>
              Already registered?
            </span>
          </div>

          <Link
            to="/login"
            className="news-auth-secondary-button"
          >
            Login to your account
          </Link>
        </div>
      </div>
    </section>
  );
}

export default Register;