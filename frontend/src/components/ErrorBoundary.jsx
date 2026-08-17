import React from 'react';
import MKCLogo from './MKCLogo';
import { RotateCcw, Home, AlertCircle } from 'lucide-react';
import './ErrorBoundary.css';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Mastery Key Coach - Caught Runtime Error:', error);
    if (error?.message) console.error('Error Message:', error.message);
    if (error?.stack) console.error('Error Stack:', error.stack);
    if (errorInfo?.componentStack) console.error('Component Stack:', errorInfo.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleGoDashboard = () => {
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="mkc-error-boundary-container">
          <div className="mkc-error-boundary-card glass-panel">
            <div className="mkc-error-logo-wrap">
              <MKCLogo width={64} height={76} />
            </div>
            
            <div className="mkc-error-badge">
              <AlertCircle size={16} />
              <span>SYSTEM NOTICE</span>
            </div>

            <h2 className="mkc-error-title">Something went wrong</h2>
            <p className="mkc-error-desc">
              Mastery Key Coach encountered an unexpected issue while rendering this section, but the platform is still running securely.
            </p>

            <div className="mkc-error-actions">
              <button 
                onClick={this.handleRetry} 
                className="mkc-btn-retry"
                title="Retry current view"
              >
                <RotateCcw size={16} />
                <span>Retry</span>
              </button>
              <button 
                onClick={this.handleGoDashboard} 
                className="mkc-btn-dashboard"
                title="Return to Dashboard"
              >
                <Home size={16} />
                <span>Return to Dashboard</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
