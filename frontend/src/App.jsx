import { useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Missions from './pages/Missions';
import Goals from './pages/Goals';
import AICoach from './pages/AICoach';
import Habits from './pages/Habits';
import Journal from './pages/Journal';
import Blueprint from './pages/Blueprint';
import Settings from './pages/Settings';
import Community from './pages/Community';
import { getSettings } from './services/api';

import './styles/globals.css';

// Immediate theme bootstrap from localStorage to prevent render flicker
const savedTheme = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', savedTheme);

function App() {
  useEffect(() => {
    let isMounted = true;
    async function syncBackendTheme() {
      try {
        const s = await getSettings();
        if (isMounted && s && s.theme) {
          document.documentElement.setAttribute('data-theme', s.theme);
          localStorage.setItem('theme', s.theme);
        }
      } catch (err) {
        console.warn('Could not sync theme settings from backend:', err);
      }
    }
    syncBackendTheme();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/missions" element={<Missions />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/coach" element={<AICoach />} />
        <Route path="/habits" element={<Habits />} />
        <Route path="/streaks" element={<Habits />} />
        <Route path="/journal" element={<Journal />} />
        <Route path="/blueprint" element={<Blueprint />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/community" element={<Community />} />
        <Route path="/landing" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;