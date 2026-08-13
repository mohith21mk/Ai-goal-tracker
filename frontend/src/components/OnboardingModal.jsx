import { useState } from 'react';
import { Target, Zap } from 'lucide-react';
import MKCLogo from './MKCLogo';
import { submitOnboarding } from '../services/api';
import './OnboardingModal.css';

export default function OnboardingModal({ onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [primaryGoal, setPrimaryGoal] = useState('AI Engineering Mastery');
  const [commitmentLevel, setCommitmentLevel] = useState('3-5 daily protocols');
  const [improvementArea] = useState('Consistency & Execution');
  const [firstMissionTitle, setFirstMissionTitle] = useState('Complete Morning Deep Work Protocol');

  const handleFinish = async () => {
    setLoading(true);
    setError('');
    try {
      await submitOnboarding({
        primary_goal: primaryGoal,
        commitment_level: commitmentLevel,
        improvement_area: improvementArea,
        first_mission_title: firstMissionTitle,
      });
      if (onComplete) onComplete();
    } catch (err) {
      setError(err.message || 'Failed to complete onboarding.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-modal glass-panel">
        <div className="onboarding-header">
          <MKCLogo size={44} className="onboarding-logo" />
          <div className="step-indicator">
            Step {step} of 5
          </div>
        </div>

        {error && <div className="login-error-alert" style={{ marginBottom: '16px' }}>{error}</div>}

        {step === 1 && (
          <div className="onboarding-step">
            <h2 className="onboarding-title font-display">Welcome to Mastery Key Coach</h2>
            <p className="onboarding-subtitle">
              Your future isn't built by motivation. It is built by disciplined, structured action repeated every single day.
            </p>
            <div className="onboarding-feature-list">
              <div className="feature-item">
                <span className="feature-icon">
                  <Target size={24} strokeWidth={1.8} aria-hidden="true" />
                </span>
                <div>
                  <strong>Life Blueprint & Goals</strong>
                  <p>Structure multi-year milestones into daily execution steps.</p>
                </div>
              </div>
              <div className="feature-item">
                <span className="feature-icon">
                  <Zap size={24} strokeWidth={1.8} aria-hidden="true" />
                </span>
                <div>
                  <strong>Real Telemetry & Analytics</strong>
                  <p>Track your actual discipline score, streak, and execution metrics.</p>
                </div>
              </div>
            </div>
            <button className="onboarding-btn-primary" onClick={() => setStep(2)}>
              Begin Setup →
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="onboarding-step">
            <h2 className="onboarding-title font-display">What are you working toward?</h2>
            <p className="onboarding-subtitle">Select your primary focus area for Mastery Key Coach.</p>
            <div className="options-grid">
              {[
                'AI Engineering & System Architecture',
                'Software Career & Technical Placement',
                'Physical Fortitude & Health Protocol',
                'Financial Mastery & Wealth Foundation',
              ].map((opt) => (
                <div
                  key={opt}
                  className={`option-card ${primaryGoal === opt ? 'selected' : ''}`}
                  onClick={() => setPrimaryGoal(opt)}
                >
                  <span className="option-radio">{primaryGoal === opt ? '●' : '○'}</span>
                  <span>{opt}</span>
                </div>
              ))}
            </div>
            <div className="onboarding-nav">
              <button className="onboarding-btn-secondary" onClick={() => setStep(1)}>Back</button>
              <button className="onboarding-btn-primary" onClick={() => setStep(3)}>Next Step →</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="onboarding-step">
            <h2 className="onboarding-title font-display">Daily Commitment Level</h2>
            <p className="onboarding-subtitle">How many daily actions can you realistically commit to?</p>
            <div className="options-grid">
              {[
                '1-2 focused protocols (Essential)',
                '3-5 daily protocols (Standard Mastery)',
                '5+ daily protocols (High Intensity)',
              ].map((opt) => (
                <div
                  key={opt}
                  className={`option-card ${commitmentLevel === opt ? 'selected' : ''}`}
                  onClick={() => setCommitmentLevel(opt)}
                >
                  <span className="option-radio">{commitmentLevel === opt ? '●' : '○'}</span>
                  <span>{opt}</span>
                </div>
              ))}
            </div>
            <div className="onboarding-nav">
              <button className="onboarding-btn-secondary" onClick={() => setStep(2)}>Back</button>
              <button className="onboarding-btn-primary" onClick={() => setStep(4)}>Next Step →</button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="onboarding-step">
            <h2 className="onboarding-title font-display">Build Your First Mission</h2>
            <p className="onboarding-subtitle">Define the first action item for your daily dashboard.</p>
            <div className="form-group" style={{ marginBottom: '20px' }}>
              <label>First Mission Title</label>
              <input
                type="text"
                value={firstMissionTitle}
                onChange={(e) => setFirstMissionTitle(e.target.value)}
                placeholder="e.g. Complete Morning Deep Work Block"
              />
            </div>
            <div className="onboarding-nav">
              <button className="onboarding-btn-secondary" onClick={() => setStep(3)}>Back</button>
              <button className="onboarding-btn-primary" onClick={() => setStep(5)}>Next Step →</button>
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="onboarding-step" style={{ textAlign: 'center' }}>
            <h2 className="onboarding-title font-display">Your MKC Dashboard is Ready</h2>
            <p className="onboarding-subtitle">
              Your personalized workspace has been configured. Start building your daily streak today.
            </p>
            <button
              className="onboarding-btn-primary"
              onClick={handleFinish}
              disabled={loading}
              style={{ width: '100%', marginTop: '16px' }}
            >
              {loading ? 'Initializing Workspace...' : 'Launch Dashboard'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
