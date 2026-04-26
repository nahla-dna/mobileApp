const express = require('express');
const cors = require('cors'); // Import CORS middleware
const app = express();
const port = 3000; // Choose a port for your backend

// In a real application, this data would come from a database
const ownersNeedingAttention = [
    { "owner_id": 1, "owner_name": "Aswin Chintaram" },
    { "owner_id": 2, "owner_name": "Babita Devi" },
    { "owner_id": 3, "owner_name": "Carlos Pereira" }
];

app.use(cors()); // Enable CORS for all origins (for development - be more specific in production)
app.use(express.json()); // To parse JSON request bodies (if needed)

app.get('/api/getOwnersNeedingAttention', (req, res) => {
    res.json(ownersNeedingAttention);
});

app.listen(port, () => {
    console.log(`Backend server listening at http://localhost:${port}`);
});