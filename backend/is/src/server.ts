/**
 * @file   server.ts
 * @brief  HTTP server entry point - binds the Express application to a port.
 * @author Adam Kinzel (xkinzea00)
 */

import app from './app';
import 'dotenv/config';

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`=========================================`);
    console.log(`Server running on port ${PORT}`);
    console.log(`http://localhost:${PORT}/api/organizations`);
    console.log(`=========================================`);
});