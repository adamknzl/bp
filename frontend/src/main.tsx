/**
 * @file  main.tsx
 * @brief React application entry point — mounts the root component into the DOM.
 * @author Adam Kinzel (xkinzea00)
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
