import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import OrganizationList from './pages/OrganizationList';
import OrganizationDetail from './pages/OrganizationDetail';

function Navigation() {
  return (
    <nav className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center sticky top-0 z-10">
      <div className="flex gap-8 items-center text-lg">
        {/* Aktívny link má hrubší font a modrú podčiarkovaciu čiaru */}
        <Link to="/" className="font-bold text-[#005A92] border-b-2 border-[#005A92] pb-1 font-['Manrope',sans-serif]">Organizations</Link>
        <Link to="/" className="text-gray-600 hover:text-gray-900 pb-1 font-medium">Database</Link>
        <Link to="/" className="text-gray-600 hover:text-gray-900 pb-1 font-medium">Contact</Link>
      </div>
      <div>
        <div className="relative">
          {/* Ikonka lupy */}
          <svg className="w-5 h-5 absolute left-4 top-2.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
          <input 
            type="text" 
            placeholder="Search name or location" 
            className="pl-11 pr-4 py-2 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-[#005A92] w-72" 
          />
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      {/* Hlavný obal celej aplikácie so špecifickým pozadím a základným fontom */}
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