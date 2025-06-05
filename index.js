const express = require('express');
const https = require('https');
const fs = require('fs');
const axios = require('axios');

const app = express();
app.use(express.json());

const options = {
    key: fs.readFileSync('selfsigned.key'),
    cert: fs.readFileSync('selfsigned.crt'),
};

app.post('/submit', async (req, res) => {
    try {
        const response = await axios.post('http://127.0.0.1:5000/submit', req.body);
        res.json(response.data);
    } catch (error) {
        console.error('Error sending request:', error.message);
        res.status(500).send('Error sending request');
    }
});

https.createServer(options, app).listen(3000, () => {
    console.log('Proxy server is running');
});
