import { NavLink, useNavigate } from "react-router-dom";

import logo from "../assets/logo.png";
import { useAuth } from "../context/AuthContext";

function Navbar({ theme, onToggleTheme }) {
  const navigate = useNavigate();

  const {
    user,
    isAuthenticated,
    logout,
  } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", {
      replace: true,
    });
  };

  const getNavLinkClass = ({ isActive }) => {
    return isActive
      ? "sidebar-link active"
      : "sidebar-link";
  };

  return (
    <aside className="sidebar">
      <div>
        <div className="brand">
          <img
            src={logo}
            alt="News Agent logo"
            className="brand-logo-img"
          />

          <div>
            <h2>News Agent</h2>
            <p>RAG INTEL PIPELINE</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {isAuthenticated ? (
            <>
              <NavLink
                to="/ask"
                className={getNavLinkClass}
              >
                <span>☁</span>
                Ask AI Agent
              </NavLink>

              <NavLink
                to="/news"
                className={getNavLinkClass}
              >
                <span>▣</span>
                Latest News
              </NavLink>

              <NavLink
                to="/briefs"
                className={getNavLinkClass}
              >
                <span>▤</span>
                Daily Briefs
              </NavLink>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={getNavLinkClass}
              >
                <span>↪</span>
                Login
              </NavLink>

              <NavLink
                to="/register"
                className={getNavLinkClass}
              >
                <span>＋</span>
                Create Account
              </NavLink>
            </>
          )}

          {/* <NavLink
            to="/subscribe"
            className={getNavLinkClass}
          >
            <span>✉</span>
            Subscribe
          </NavLink> */}
        </nav>
      </div>

      <div className="sidebar-footer">
        {isAuthenticated && (
          <div className="sidebar-user-card">
            <div className="sidebar-user-avatar">
              {user?.name
                ? user.name
                    .trim()
                    .charAt(0)
                    .toUpperCase()
                : "U"}
            </div>

            <div className="sidebar-user-details">
              <strong>
                {user?.name || "User"}
              </strong>

              <span title={user?.email}>
                {user?.email}
              </span>
            </div>
          </div>
        )}

        <div className="agent-status">
          <span className="agent-status-dot" />
          AGENT STATUS: ONLINE
        </div>

        <button
          type="button"
          className="theme-toggle"
          onClick={onToggleTheme}
        >
          <span>
            {theme === "dark" ? "☀️" : "🌙"}
          </span>

          {theme === "dark"
            ? "Light Mode"
            : "Dark Mode"}
        </button>

        {isAuthenticated && (
          <button
            type="button"
            className="sidebar-logout-button"
            onClick={handleLogout}
          >
            <span>↩</span>
            Logout
          </button>
        )}
      </div>
    </aside>
  );
}

export default Navbar;