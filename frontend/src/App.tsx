import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import TransactionList from "./pages/TransactionList";
import AlertCenter from "./pages/AlertCenter";
import Analytics from "./pages/Analytics";

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <h1 className="text-6xl font-bold text-slate-700">404</h1>
      <p className="mt-4 text-lg text-slate-400">Page not found</p>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/transactions" element={<TransactionList />} />
        <Route path="/alerts" element={<AlertCenter />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
