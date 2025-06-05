const express = require('express');
const axios = require('axios');
const app = express();

// Enable CORS for all origins
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// Proxy endpoint
app.get('/*', async (req, res) => {
  const targetUrl = req.url.slice(1);
  if (!targetUrl) {
    return res.status(400).json({ error: 'No target URL provided' });
  }

  try {
    const response = await axios.get(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://allinonereborn.com',
        'Origin': 'https://allinonereborn.com',
        'X-Requested-With': 'XMLHttpRequest'
      },
      responseType: 'stream'
    });

    Object.entries(response.headers).forEach(([key, value]) => {
      res.setHeader(key, value);
    });

    response.data.pipe(res);
  } catch (error) {
    console.error('Proxy error:', {
      url: targetUrl,
      message: error.message,
      status: error.response?.status
    });
    res.status(error.response?.status || 500).json({
      error: 'Proxy failed',
      message: error.message
    });
  }
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`CORS proxy running on port ${port}`);
});
