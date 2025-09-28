const express = require("express");
const app = express();
const port = process.env.PORT || 3000;  // Azure injects PORT

app.use(express.static("Public"));

app.get("/", (req, res) => {
    res.sendFile(__dirname + "/Public/index.html");
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
