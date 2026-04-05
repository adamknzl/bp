import express, { Application } from 'express';
import cors from 'cors';
import orgRoutes from './routes/org.routes';

const app: Application = express();

app.use(cors());
app.use(express.json());

app.use('/api/organizations', orgRoutes);

export default app;