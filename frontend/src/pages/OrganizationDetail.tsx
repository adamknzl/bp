import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

interface Category {
  category_id: string;
  name: string;
}

interface Branch {
  branch_id: string;
  city: string | null;
  street: string | null;
  email: string | null;
  tel_num: string | null;
  lat: number | null;
  lon: number | null;
}

interface OrganizationDetail {
  organization_id: string;
  name: string;
  ico: string;
  legal_form: string | null;
  description: string | null;
  web_url: string | null;
  emails: string[];
  tel_numbers: string[];
  organization_category?: {
    category: Category
  }[];
  branches?: Branch[];
}

const getCategoryColor = (categoryName: string) => {
  const colors: Record<string, string> = {
    'Seniors': 'bg-[#E2F5EA] text-[#2D6A4F]',
    'Social care': 'bg-red-100 text-red-700',
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
    'Senior support': 'bg-[#E2F5EA] text-[#2D6A4F]',
    'Social services': 'bg-red-100 text-red-700',
    'Sports': 'bg-green-100 text-green-700',
    'Youth': 'bg-rose-100 text-rose-700'
  };

  return colors[categoryName] || colors['Other'];
};

export default function OrganizationDetail() {
  const { id } = useParams<{ id: string }>(); 
  const [org, setOrg] = useState<OrganizationDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const response = await fetch(`http://localhost:3000/api/organizations/${id}`);
        if (!response.ok) {
          if (response.status === 404) throw new Error("Organizácia sa nenašla");
          throw new Error("Chyba pri sťahovaní detailu");
        }
        
        const result = await response.json();
        setOrg(result.data || result); 
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchDetail();
  }, [id]);

  if (loading) return <div className="p-12 text-center text-gray-500 font-medium">Načítavam detail...</div>;
  if (error) return <div className="p-12 text-center text-red-500 font-bold">{error}</div>;
  if (!org) return null;

  return (
    <div className="min-h-screen bg-[#F8F9FA] pb-20">
      <div className="max-w-[1200px] mx-auto px-8 pt-10">
        
        {/* Back navigation */}
        <Link to="/" className="text-gray-500 hover:text-[#005A92] transition text-sm flex items-center gap-2 mb-6">
          <span>&larr;</span> back to search results
        </Link>

        {/* Header */}
        <div className="mb-10">
          <h1 className="text-4xl md:text-4xl font-extrabold text-[#005A92] font-['Manrope',sans-serif] mb-4">
            {org.name}
          </h1>
          <div className="flex gap-2 flex-wrap">
             {org.organization_category?.map((oc) => {
               const colorClass = getCategoryColor(oc.category.name);
               return (
                 <span 
                   key={oc.category.category_id} 
                   className={`px-3 py-1.5 text-xs font-bold rounded-full uppercase tracking-wider ${colorClass}`}
                 >
                   {oc.category.name}
                 </span>
               );
             })}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          
          {/* Left Column (Description & Branches) */}
          <div className="lg:col-span-2 space-y-12">
            
            {/* Description */}
            <section>
              <h2 className="text-2xl font-bold text-[#005A92] font-['Manrope',sans-serif] mb-4">Description</h2>
              <div className="text-gray-700 leading-relaxed text-base">
                {org.description ? (
                  <p>{org.description}</p>
                ) : (
                  <p className="italic opacity-60">Organizácia zatiaľ neposkytla bližší popis svojej činnosti.</p>
                )}
              </div>
            </section>

            {/* Branches */}
            <section>
              <h2 className="text-2xl font-bold text-[#005A92] font-['Manrope',sans-serif] mb-6">Branches</h2>
              
              {/* Map Placeholder */}
              <div className="w-full h-64 bg-gray-200 rounded-xl mb-6 flex items-center justify-center text-gray-400">
                [ Map Placeholder - Integration with Google Maps / Leaflet ]
              </div>

              {/* Branch List */}
              <div className="space-y-4">
                {org.branches && org.branches.length > 0 ? (
                  org.branches.map((branch, index) => (
                    <div key={branch.branch_id} className="bg-white p-5 rounded-xl flex items-center gap-5 shadow-sm border border-gray-100">
                      <div className="w-12 h-12 rounded-lg bg-[#E2F5EA] text-[#2D6A4F] flex items-center justify-center flex-shrink-0">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                      </div>
                      <div className="flex-grow">
                        <h4 className="text-lg font-bold text-gray-900">{branch.city || "Pobočka"}</h4>
                        <p className="text-gray-500 text-sm">{branch.street || "Adresa neuvedená"}</p>
                      </div>
                      <div className="hidden sm:block text-xs font-bold text-gray-500">
                        {index === 0 ? "Hlavní ústředí" : "Pobočka"}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 italic">Táto organizácia nemá evidované žiadne pobočky.</p>
                )}
              </div>
            </section>
          </div>

          {/* Right Column (Contact Info) */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 sticky top-24">
              <h3 className="text-2xl font-bold text-[#005A92] font-['Manrope',sans-serif] border-b border-gray-100 pb-4 mb-6">
                Contact info
              </h3>

              <div className="space-y-8">
                
                {/* Emails */}
                <div>
                  <div className="flex items-center gap-2 text-gray-400 mb-3 uppercase tracking-wider text-xs font-bold">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                    E-mail addresses
                  </div>
                  <div className="space-y-2 ml-6 text-sm font-medium text-[#005A92]">
                    {org.emails && org.emails.length > 0 ? (
                      org.emails.map((email, idx) => (
                        <a key={idx} href={`mailto:${email}`} className="block hover:underline">{email}</a>
                      ))
                    ) : (
                      <span className="text-gray-500">Neuvedené</span>
                    )}
                  </div>
                </div>

                {/* Phones */}
                <div>
                  <div className="flex items-center gap-2 text-gray-400 mb-3 uppercase tracking-wider text-xs font-bold">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"></path></svg>
                    Telephone contacts
                  </div>
                  <div className="space-y-2 ml-6 text-sm font-medium text-gray-800">
                    {org.tel_numbers && org.tel_numbers.length > 0 ? (
                      org.tel_numbers.map((phone, idx) => (
                        <a key={idx} href={`tel:${phone}`} className="block hover:text-[#005A92]">{phone}</a>
                      ))
                    ) : (
                      <span className="text-gray-500">Neuvedené</span>
                    )}
                  </div>
                </div>

                {/* Website */}
                <div>
                  <div className="flex items-center gap-2 text-gray-400 mb-3 uppercase tracking-wider text-xs font-bold">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path></svg>
                    Website
                  </div>
                  <div className="space-y-2 ml-6 text-sm font-medium text-[#005A92]">
                    {org.web_url ? (
                      <a href={org.web_url.startsWith('http') ? org.web_url : `https://${org.web_url}`} target="_blank" rel="noopener noreferrer" className="block hover:underline">
                        {org.web_url.replace(/^https?:\/\//, '')}
                      </a>
                    ) : (
                      <span className="text-gray-500">Neuvedené</span>
                    )}
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}