/**
 * @file  api.ts
 * @brief Base URL configuration for all API requests.
 * @author Adam Kinzel (xkinzea00)
 *
 * The URL is read from an environment variable at build time.
 * Falls back to the local development server when the variable is not set.
 */

/// <reference types="vite/client" />

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api';