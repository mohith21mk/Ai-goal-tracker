import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Goals from './pages/Goals';

import './styles/globals.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/landing" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;