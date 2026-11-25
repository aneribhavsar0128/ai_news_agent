import { useState } from "react";
import { subscribeUser } from "../api/api";

function Subscribe() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
  });

  const [status, setStatus] = useState({
    type: "",
    message: "",
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const cleanedEmail = formData.email.trim();
    const cleanedName = formData.name.trim();

    if (!cleanedEmail) {
      setStatus({
        type: "error",
        message: "Please enter your email address.",
      });
      return;
    }

    try {
      setLoading(true);
      setStatus({
        type: "",
        message: "",
      });

      const response = await subscribeUser({
        name: cleanedName || null,
        email: cleanedEmail,
      });

      setStatus({
        type: "success",
        message: `${response.data.email} subscribed successfully.`,
      });

      setFormData({
        name: "",
        email: "",
      });
    } catch (error) {
      const apiMessage =
        error.response?.data?.detail ||
        error.response?.data?.message;

      setStatus({
        type: "error",
        message:
          typeof apiMessage === "string"
            ? apiMessage
            : "Subscription failed. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="subscribe-page">
      <div className="subscribe-card">
        <div className="subscribe-badge">
          Daily AI Newsletter
        </div>

        <h1>Get the important news every morning</h1>

        <p className="subscribe-description">
          Receive a concise AI-generated briefing covering India,
          world affairs, technology, business, health and science.
        </p>

        <form
          className="subscribe-form"
          onSubmit={handleSubmit}
        >
          <label htmlFor="subscriber-name">
            Name
          </label>

          <input
            id="subscriber-name"
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Enter your name"
            maxLength={100}
          />

          <label htmlFor="subscriber-email">
            Email address
          </label>

          <input
            id="subscriber-email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="you@example.com"
            required
          />

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Subscribing..."
              : "Subscribe to Daily Brief"}
          </button>
        </form>

        {status.message && (
          <div
            className={`subscribe-message ${status.type}`}
          >
            {status.message}
          </div>
        )}

        <p className="subscribe-note">
          You can unsubscribe at any time.
        </p>
      </div>
    </section>
  );
}

export default Subscribe;