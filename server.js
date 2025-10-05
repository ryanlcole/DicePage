import express from "express";
import compression from "compression";
import helmet from "helmet";
import morgan from "morgan";
const app = express(
const PORT = process.env.PORT || 3000;
app.use(helmet());
app.use(compression());
app.use(morgan("dev"));
app.use(express.static("Public"));
