/**
 * @file  App.tsx
 * @brief Root application component — sets up routing and the top navigation bar.
 * @author Adam Kinzel (xkinzea00)
 */

import { useState, useEffect } from 'react';
import {
  BrowserRouter, Routes, Route,
  Link, useNavigate, useSearchParams, useLocation,
} from 'react-router-dom';
import 'leaflet/dist/leaflet.css';

import OrganizationList   from './pages/OrganizationList';
import OrganizationDetail from './pages/OrganizationDetail';


// ─── Navigation ───────────────────────────────────────────────────────────────

/** Keys used by the filter persistence layer — kept in sync with useOrganizations. */
const FILTER_SESSION_KEYS = [
  'org_filter_size',
  'org_filter_legal_form',
  'org_filter_categories',
] as const;

function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') ?? '');

  // Keep the input in sync when the user navigates back/forward.
  useEffect(() => {
    setSearchTerm(searchParams.get('search') ?? '');
  }, [searchParams]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = searchTerm.trim();
    navigate(trimmed ? `/?search=${encodeURIComponent(trimmed)}` : '/');
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    navigate('/');
  };

  /**
   * Navigate to the homepage and reset all filter + search state.
   * If the user is already on the homepage with no active search, force a
   * full reload to reset the React state inside OrganizationList.
   */
  const handleLogoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    FILTER_SESSION_KEYS.forEach(k => sessionStorage.removeItem(k));
    setSearchTerm('');
    navigate('/', { replace: true });

    if (location.pathname === '/' && !location.search) {
      window.location.reload();
    }
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center sticky top-0 z-[10000]">

      <div className="flex gap-8 items-center text-xl">
        <Link
          to="/"
          onClick={handleLogoClick}
          className="font-black text-brand font-['Manrope',sans-serif] hover:text-blue-800 transition"
        >
          nezisk.cz
        </Link>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 items-center">
        <div className="relative flex items-center">
          <svg className="w-5 h-5 absolute left-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>

          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Hledat (název, místo, IČO)"
            className="pl-11 pr-10 py-2 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-brand w-72 transition-all"
          />

          {searchTerm && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute right-3 p-1 text-gray-400 hover:text-gray-700 transition rounded-full focus:outline-none"
              title="Vymazat vyhledávání"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        <button
          type="submit"
          className="px-5 py-2 bg-brand text-white text-sm font-bold rounded-full hover:bg-blue-800 transition shadow-sm cursor-pointer"
        >
          Vyhledat
        </button>
      </form>

    </nav>
  );
}


// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#F8F9FA] font-['Inter',sans-serif] text-gray-800">
        <Navigation />
        <Routes>
          <Route path="/"        element={<OrganizationList />} />
          <Route path="/org/:id" element={<OrganizationDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}