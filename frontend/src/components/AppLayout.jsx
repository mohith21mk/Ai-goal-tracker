import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-viewport">
        <TopBar />
        <Outlet />
      </div>
    </div>
  );
}
