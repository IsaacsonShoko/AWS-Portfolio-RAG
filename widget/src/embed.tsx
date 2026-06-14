import React from "react";
import ReactDOM from "react-dom/client";
import { FourDAssistant, type FourDAssistantProps } from "./components/FourDAssistant";
import "./index.css";

export function mountFourDAssistant(selector: string, props: FourDAssistantProps = {}) {
  const el = document.querySelector(selector);
  if (!el) throw new Error(`mountFourDAssistant: no element matches ${selector}`);
  ReactDOM.createRoot(el).render(
    <React.StrictMode>
      <FourDAssistant {...props} />
    </React.StrictMode>,
  );
}

// Auto-mount if a #fourd-assistant container exists (drop-in script usage).
if (typeof document !== "undefined") {
  const auto = document.getElementById("fourd-assistant");
  if (auto) mountFourDAssistant("#fourd-assistant");
}
