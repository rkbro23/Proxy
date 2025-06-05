const express = require('express');
const axios = require('axios');
const app = express();

// Enable CORS for all origins
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  res.header('Access-Control-Expose-Headers', 'Content-Length, Content-Type');
  next();
});

// Logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] Request: ${req.method} ${req.url}`);
  next();
});

// Proxy endpoint
app.get('/*', async (req, res) => {
  const targetUrl = req.url.slice(1);
  if (!targetUrl) {
    console.error(`[${new Date().toISOString()}] No target URL provided`);
    return res.status(400).json({ error: 'No target URL provided' });
  }

  try {
    const response = await axios.get(targetUrl, {
      headers: {
        'User-Agent': 'OTT Navigator/1.6.9.4 (Android)', // Mimic OTT Navigator
        'Referer': 'https://allinonereborn.com',
        'Origin': 'https://allinonereborn.com',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Connection': 'keep-alive'
      },
      responseType: 'stream',
      maxRedirects: 5,
      timeout: 10000 // 10s timeout
    });

    // Forward headers
    const excludedHeaders = ['transfer-encoding', 'connection', 'host'];
    Object.entries(response.headers).forEach(([key, value]) => {
      if (!excludedHeaders.includes(key.toLowerCase())) {
        res.setHeader(key, value);
      }
    });
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Expose-Headers', 'Content-Length, Content-Type');

    console.log(`[${new Date().toISOString()}] Success: ${targetUrl}, Status: ${response.status}`);

    // Stream response
    response.data.pipe(res);

    // Handle stream errors
    response.data.on('error', (err) => {
      console.error(`[${new Date().toISOString()}] Stream error: ${targetUrl}`, err.message);
      res.status(500).json({ error: 'Stream failed', message: err.message });
    });
  } catch (error) {
    const status = error.response?.status || 500;
    console.error(`[${new Date().toISOString()}] Proxy error: ${targetUrl}`, {
      message: error.message,
      status,
      response: error.response?.data
    });
    res.status(status).json({
      error: 'Proxy failed',
      message: error.message
    });
  }
});

// Start server
const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`Beast Mode CORS Proxy running on port ${port}`);
});
