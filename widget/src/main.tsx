import React from "react";
import ReactDOM from "react-dom/client";
import { FourDAssistant } from "./components/FourDAssistant";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <FourDAssistant repos={["sim-conveyor-vision", "chefmind-ai", "xlink-inventory"]} />
  </React.StrictMode>,
);
