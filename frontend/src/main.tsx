import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

function App() {
  return (
    <main>
      <h1>IronMan</h1>
      <p>Personal investment operating system foundation.</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
