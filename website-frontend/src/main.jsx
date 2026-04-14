import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorMessage: '' };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, errorMessage: error?.message || 'Unknown frontend error' };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[Frontend] Unhandled render error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#020202',
          color: '#e2e8f0',
          fontFamily: 'system-ui, sans-serif',
          padding: '24px',
        }}>
          <div style={{
            maxWidth: '560px',
            width: '100%',
            background: 'rgba(10,10,10,0.9)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: '16px',
            padding: '20px',
          }}>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '22px' }}>Dashboard failed to render</h2>
            <p style={{ margin: '0 0 10px 0', color: '#94a3b8' }}>
              Please refresh this page. If it still fails, open a fresh Dashboard link from Telegram.
            </p>
            <p style={{ margin: 0, color: '#fda4af', fontSize: '13px', wordBreak: 'break-word' }}>
              {this.state.errorMessage}
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
)
