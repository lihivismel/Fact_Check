// main.jsx
// Entry point that mounts the React App into the HTML page.

import React from "react";                     // Enables JSX and React features
import { createRoot } from "react-dom/client"; // Modern API to render React
import App from "./App.jsx";                   // Main App component
import "./index.css";                          // Load Tailwind v4 (via PostCSS) + global CSS

const root = createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
