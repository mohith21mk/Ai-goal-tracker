import { useState, useEffect, useRef, useCallback } from 'react';

export const ConnectionStatus = {
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  DISCONNECTED: 'DISCONNECTED',
  RECONNECTING: 'RECONNECTING',
  ERROR: 'ERROR',
};

export function useMessagingSocket(onMessageReceived) {
  const [status, setStatus] = useState(ConnectionStatus.DISCONNECTED);
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const processedMessageIds = useRef(new Set());
  const connectRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const isMountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setStatus(reconnectAttemptsRef.current > 0 ? ConnectionStatus.RECONNECTING : ConnectionStatus.CONNECTING);

    let wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      const defaultApiUrl = import.meta.env.PROD 
        ? 'https://mkc-backend-iguj.onrender.com' 
        : 'http://localhost:8000';
      const apiUrl = import.meta.env.VITE_API_URL || defaultApiUrl;
      if (apiUrl.startsWith('http')) {
        wsUrl = apiUrl.replace(/^http/, 'ws') + '/api/chat/ws';
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${protocol}//${host}/api/chat/ws`;
      }
    }

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        if (!isMountedRef.current) return;
        setStatus(ConnectionStatus.CONNECTED);
        reconnectAttemptsRef.current = 0;
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'message.created' || data.type === 'new_message') {
            const msgObj = data.message || data;
            const msgId = msgObj.id;

            if (msgId && processedMessageIds.current.has(msgId)) {
              return; // Prevent duplicate rendering
            }
            if (msgId) {
              if (processedMessageIds.current.size > 500) {
                const idsArray = Array.from(processedMessageIds.current);
                processedMessageIds.current = new Set(idsArray.slice(250));
              }
              processedMessageIds.current.add(msgId);
            }

            if (onMessageReceived && isMountedRef.current) {
              onMessageReceived(data);
            }
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      socket.onerror = (err) => {
        console.warn('WebSocket error:', err);
        if (isMountedRef.current) {
          setStatus(ConnectionStatus.ERROR);
        }
      };

      socket.onclose = () => {
        if (!isMountedRef.current) return;
        setStatus(ConnectionStatus.DISCONNECTED);
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const timeout = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current += 1;
          if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = setTimeout(() => {
            if (connectRef.current && isMountedRef.current) connectRef.current();
          }, timeout);
        }
      };
    } catch (err) {
      console.error('WebSocket connection setup failed:', err);
      if (isMountedRef.current) {
        setStatus(ConnectionStatus.ERROR);
      }
    }
  }, [onMessageReceived]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    isMountedRef.current = true;
    connect();
    return () => {
      isMountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((conversationId, content) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not connected. Message send postponed.');
      return false;
    }

    const payload = {
      type: 'message.send',
      conversation_id: conversationId,
      content: content.trim(),
      message: content.trim(),
    };

    wsRef.current.send(JSON.stringify(payload));
    return true;
  }, []);

  return {
    status,
    sendMessage,
    isConnected: status === ConnectionStatus.CONNECTED,
  };
}
