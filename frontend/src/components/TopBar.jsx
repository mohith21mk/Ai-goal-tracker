import { useState } from 'react';
import './TopBar.css';

const TopBar = () => {
  const [searchValue, setSearchValue] = useState('');

  return (
    <header className="topbar-container">
      {/* Search Input Field */}
      <div className="topbar-search glass-panel">
        <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          type="text"
          placeholder="Search goals, habits, insights..."
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          className="search-input"
        />
        <kbd className="search-shortcut">⌘K</kbd>
      </div>

      {/* Right User & AI Status Area */}
      <div className="topbar-actions">
        {/* AI Coach Online Pill */}
        <div className="ai-status-pill">
          <span className="pulsing-dot" />
          <span className="ai-status-text">AI Coach Online</span>
        </div>

        {/* User Profile & Badge */}
        <div className="user-profile-wrapper glass-panel">
          <div className="user-level-badge">
            <span className="badge-star">⚡</span>
            <span className="badge-text">Level 8 Champion</span>
          </div>
          <div className="avatar-wrapper">
            <svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="18" cy="18" r="17" fill="#071426" stroke="#38BDF8" strokeWidth="1.5"/>
              <circle cx="18" cy="13" r="6" fill="#38BDF8" fillOpacity="0.8"/>
              <path d="M7 30C7 24.4772 11.4772 20 17 20H19C24.5228 20 29 24.4772 29 30V32H7V30Z" fill="#3B82F6" fillOpacity="0.6"/>
            </svg>
            <span className="avatar-online-dot" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
