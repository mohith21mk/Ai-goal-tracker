import { useState, useEffect, useRef, useCallback } from 'react';

export const ConnectionStatus = {
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  DISCONNECTED: 'DISCONNECTED',
  RECONNECTING: 'RECONNECTING',
  ERROR: 'ERROR',
};

export function useNotificationsSocket(onNotificationReceived) {
  const [status, setStatus] = useState(ConnectionStatus.DISCONNECTED);
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const processedNotifIds = useRef(new Set());
  const connectRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setStatus(reconnectAttemptsRef.current > 0 ? ConnectionStatus.RECONNECTING : ConnectionStatus.CONNECTING);

    let wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      const defaultApiUrl = import.meta.env.PROD 
        ? 'https://mkc-backend-iguj.onrender.com' 
        : 'http://localhost:8000';
      let apiUrl = import.meta.env.VITE_API_URL || defaultApiUrl;
      if (import.meta.env.PROD && (apiUrl.includes('your-backend-service') || apiUrl.includes('localhost'))) {
        apiUrl = defaultApiUrl;
      }
      if (apiUrl.startsWith('http')) {
        wsUrl = apiUrl.replace(/^http/, 'ws') + '/api/notifications/ws';
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${protocol}//${host}/api/notifications/ws`;
      }
    }

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setStatus(ConnectionStatus.CONNECTED);
        reconnectAttemptsRef.current = 0;
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'new_notification' || data.event === 'notification') {
            const notifObj = data.notification || data;
            const notifId = notifObj.id;

            if (notifId && processedNotifIds.current.has(notifId)) {
              return; // Prevent duplicate rendering
            }
            if (notifId) {
              if (processedNotifIds.current.size > 300) {
                const idsArray = Array.from(processedNotifIds.current);
                processedNotifIds.current = new Set(idsArray.slice(150));
              }
              processedNotifIds.current.add(notifId);
            }

            if (onNotificationReceived) {
              onNotificationReceived(notifObj);
            }
          }
        } catch (err) {
          console.error('Failed to parse notification WebSocket message:', err);
        }
      };

      socket.onerror = (err) => {
        console.warn('Notification WebSocket error:', err);
        setStatus(ConnectionStatus.ERROR);
      };

      socket.onclose = () => {
        setStatus(ConnectionStatus.DISCONNECTED);
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const timeout = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;
          setTimeout(() => {
            if (connectRef.current) connectRef.current();
          }, timeout);
        }
      };
    } catch (err) {
      console.error('Notification WebSocket connection setup failed:', err);
      setStatus(ConnectionStatus.ERROR);
    }
  }, [onNotificationReceived]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    status,
    isConnected: status === ConnectionStatus.CONNECTED,
  };
}
