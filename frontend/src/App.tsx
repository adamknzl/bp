import { BrowserRouter, Routes, Route, Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import 'leaflet/dist/leaflet.css';
import OrganizationList from './pages/OrganizationList';
import OrganizationDetail from './pages/OrganizationDetail';

function Navigation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');

  useEffect(() => {
    setSearchTerm(searchParams.get('search') || '');
  }, [searchParams]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/?search=${encodeURIComponent(searchTerm.trim())}`);
    } else {
      navigate(`/`);
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    navigate(`/`);
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center sticky top-0 z-[10000]">
      <div className="flex gap-8 items-center text-lg">
        <Link to="/" className="font-bold text-[#005A92] border-b-2 border-[#005A92] pb-1 font-['Manrope',sans-serif]">Organizations</Link>
        <Link to="/" className="text-gray-600 hover:text-gray-900 pb-1 font-medium">Database</Link>
        <Link to="/" className="text-gray-600 hover:text-gray-900 pb-1 font-medium">Contact</Link>
      </div>
      <div>
        <form onSubmit={handleSearch} className="flex gap-2 items-center">
          <div className="relative flex items-center">
            <svg className="w-5 h-5 absolute left-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            
            <input 
              type="text" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search name or location" 
              className="pl-11 pr-10 py-2 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-[#005A92] w-72 transition-all" 
            />

            {searchTerm && (
              <button 
                type="button" 
                onClick={handleClearSearch}
                className="absolute right-3 p-1 text-gray-400 hover:text-gray-700 transition rounded-full focus:outline-none"
                title="Vymazať vyhľadávanie"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            )}
          </div>
          
          <button 
            type="submit" 
            className="px-5 py-2 bg-[#005A92] text-white text-sm font-bold rounded-full hover:bg-blue-800 transition shadow-sm cursor-pointer"
          >
            Vyhľadať
          </button>
        </form>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#F8F9FA] font-['Inter',sans-serif] text-gray-800">
        <Navigation />
        <Routes>
          <Route path="/" element={<OrganizationList />} />
          <Route path="/org/:id" element={<OrganizationDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;