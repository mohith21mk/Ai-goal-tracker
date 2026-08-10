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

import './styles/globals.css';

function App() {
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