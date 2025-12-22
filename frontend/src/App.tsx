// Main App component with routing
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar, ErrorBoundary } from './components';
import { Home, Listings, ValueAnalysis, About } from './pages';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className="min-h-screen bg-black">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/home" element={<Home />} />
            <Route path="/dashboard" element={<Home />} />
            <Route path="/listings" element={<Listings />} />
            <Route path="/value" element={<ValueAnalysis />} />
            <Route path="/about" element={<About />} />
            {/* Catch-all for SPA */}
            <Route path="*" element={<Home />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
