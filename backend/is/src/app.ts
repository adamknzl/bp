/**
 * @file   app.ts
 * @brief  Express application factory - registers middleware and mounts route modules.
 * @author Adam Kinzel (xkinzea00)
 */

import express, { Application } from 'express';
import cors from 'cors';
import orgRoutes from './routes/org.routes';

const app: Application = express();

app.use(cors());
app.use(express.json());

// All organization-related endpoints are grouped under /api/organizations.
app.use('/api/organizations', orgRoutes);

export default app;