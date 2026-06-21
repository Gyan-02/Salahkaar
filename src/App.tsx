import { Route, Routes } from "react-router-dom";
import { Header } from "./components/Header";
import { CheckFlow } from "./pages/CheckFlow";
import { DemoCases } from "./pages/DemoCases";
import { Guidelines } from "./pages/Guidelines";
import { Home } from "./pages/Home";

function Footer() {
  return (
    <footer>
      <div className="page-shell">
        <div>
          <strong>Salahkaar</strong>
          <p>A local benefits-readiness demonstration for Bihar.</p>
        </div>
        <p>
          Not an official government portal. No approval decisions are made
          here.
        </p>
      </div>
    </footer>
  );
}
export default function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/check" element={<CheckFlow />} />
        <Route path="/demos" element={<DemoCases />} />
        <Route path="/guidelines" element={<Guidelines />} />
      </Routes>
      <Footer />
    </>
  );
}
