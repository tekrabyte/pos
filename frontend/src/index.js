import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress WebSocket errors in console (dev hot reload)
const originalConsoleError = console.error;
console.error = (...args) => {
  // Filter out WebSocket-related errors
  const errorMessage = args.join(' ');
  if (
    errorMessage.includes('WebSocket connection') ||
    errorMessage.includes('wss://') ||
    errorMessage.includes('ws://') ||
    errorMessage.includes('WebSocket error')
  ) {
    return; // Suppress WebSocket errors
  }
  originalConsoleError.apply(console, args);
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
