import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage.jsx';

// Placeholder pages 
function ComingSoon({ title }) {
  return (
    <main style={{ padding: 24 }}>
      <h1>{title}</h1>
      <p>Coming soon.</p>
    </main>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/plan" element={<ComingSoon title="Training plan" />} />
      <Route path="/stats" element={<ComingSoon title="Statistics" />} />
      <Route path="/login" element={<ComingSoon title="Log in" />} />
    </Routes>
  );
}
