import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface Category {
  category_id: string;
  name: string;
}

interface SizeCategory {
  cat_id: string;
  label: string;
}

interface Organization {
  organization_id: string;
  name: string;
  ico: string;
  legal_form: string | null;
  organization_category?: {
    category: Category
  }[];
}

const getCategoryColor = (categoryName: string) => {
  const colors: Record<string, string> = {
    'Animal welfare': 'bg-amber-100 text-amber-700',
    'Arts & creative activities': 'bg-fuchsia-100 text-fuchsia-700',
    'Charity & fundraising': 'bg-blue-100 text-blue-700',
    'Community development': 'bg-indigo-100 text-indigo-700',
    'Culture': 'bg-purple-100 text-purple-700',
    'Disability support': 'bg-cyan-100 text-cyan-700',
    'Education': 'bg-yellow-100 text-yellow-700',
    'Environment': 'bg-emerald-100 text-emerald-700',
    'Healthcare': 'bg-red-100 text-red-700',
    'Human rights': 'bg-orange-100 text-orange-700',
    'Other': 'bg-gray-100 text-gray-700',
    'Senior support': 'bg-teal-100 text-teal-700',
    'Social services': 'bg-sky-100 text-sky-700',
    'Sports': 'bg-green-100 text-green-700',
    'Youth': 'bg-rose-100 text-rose-700'
  };

  return colors[categoryName] || colors['Other'];
};

export default function OrganizationList() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sizes, setSizes] = useState<SizeCategory[]>([]);
  
  const [showAllCategories, setShowAllCategories] = useState<boolean>(false);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [orgsRes, filtersRes] = await Promise.all([
          fetch('http://localhost:3000/api/organizations'),
          fetch('http://localhost:3000/api/organizations/filters')
        ]);

        if (!orgsRes.ok || !filtersRes.ok) throw new Error("Error while downloading data.");
        
        const orgsResult = await orgsRes.json();
        const filtersResult = await filtersRes.json();

        setOrganizations(orgsResult.data);
        setCategories(filtersResult.data.categories);
        setSizes(filtersResult.data.sizes);

      } catch (err) {
        setError("Unable to load data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="p-12 text-center text-gray-500 font-medium">Loading data...</div>;
  if (error) return <div className="p-12 text-center text-red-500 font-bold">{error}</div>;

  const displayedCategories = showAllCategories ? categories : categories.slice(0, 4);

  return (
    <div className="max-w-[1400px] mx-auto p-8">
      <h1 className="text-4xl font-extrabold text-[#005A92] mb-8 font-['Manrope',sans-serif]">Non-profits overview</h1>
      
      <div className="flex flex-col lg:flex-row gap-8">
        
        {/* Filters */}
        <aside className="w-full lg:w-1/4 lg:sticky lg:top-24 self-start">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold text-[#005A92] mb-6 font-['Manrope',sans-serif]">Filters</h2>
            
            <div className="mb-6">
              <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">Region</label>
              <select className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded text-gray-700 text-sm focus:outline-none">
                <option>All regions</option>
              </select>
            </div>
            
            <div className="mb-6">
              <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">Size Category</label>
              <select className="w-full p-2.5 bg-gray-50 border border-gray-200 rounded text-gray-700 text-sm focus:outline-none">
                <option value="">All sizes</option>
                {sizes.map((size) => (
                  <option key={size.cat_id} value={size.cat_id}>
                    {size.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="mb-8">
              <label className="block text-xs font-bold text-gray-500 mb-3 uppercase tracking-wider">Kategorie</label>
              <div className="space-y-3">
                {displayedCategories.map((category) => (
                  <label key={category.category_id} className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      value={category.category_id}
                      className="w-4 h-4 rounded border-gray-300 text-[#005A92] focus:ring-[#005A92]" 
                    />
                    <span className="text-sm text-gray-700">{category.name}</span>
                  </label>
                ))}
              </div>
              
              {/* Show more categories */}
              {categories.length > 4 && (
                <button 
                  onClick={() => setShowAllCategories(!showAllCategories)}
                  className="mt-3 text-sm text-[#005A92] font-bold hover:underline focus:outline-none"
                >
                  {showAllCategories ? '- Zobraziť menej' : '+ Zobraziť všetky'}
                </button>
              )}
            </div>
            
            <button className="w-full py-3 bg-[#005A92] text-white font-semibold rounded hover:bg-blue-800 transition">
              Použít filtry
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="w-full lg:w-3/4">
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {organizations.map((org) => (
              <div key={org.organization_id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex flex-col h-full hover:shadow-md transition-shadow">
                <div className="flex gap-2 mb-4 flex-wrap">
                   {/* Category tags */}
                   {org.organization_category?.map((oc) => {
                     const colorClass = getCategoryColor(oc.category.name);
                     return (
                       <span 
                         key={oc.category.category_id} 
                         className={`px-2.5 py-1 text-[10px] font-bold rounded-full uppercase ${colorClass}`}
                       >
                         {oc.category.name}
                       </span>
                     );
                   })}
                </div>
                <h3 className="text-xl font-bold text-[#005A92] mb-3 font-['Manrope',sans-serif] leading-tight">{org.name}</h3>
                <p className="text-gray-500 text-sm mb-6 flex-grow leading-relaxed">
                  Informácie o poslaní tejto organizácie momentálne dopĺňame z našej databázy.
                </p>
                <Link 
                  to={`/org/${org.organization_id}`}
                  className="w-full py-2.5 bg-[#E9F1FF] text-[#00426D] text-center font-bold rounded hover:text-white hover:bg-[#00426D] transition text-sm"
                >
                  Zobrazit detail
                </Link>
              </div>
            ))}
          </div>
        </main>

      </div>
    </div>
  );
}