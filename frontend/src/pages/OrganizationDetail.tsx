import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

// Sem si neskôr pridaj ďalšie polia, ktoré máš v databáze (adresa, štatutár, atď.)
interface OrganizationDetail {
  organization_id: string;
  name: string;
  ico: string;
  legal_form: string;
  // hq_address?: string;
  // created_at?: string;
}

export default function OrganizationDetail() {
  // useParams vytiahne :id z URL adresy
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
        // Záleží, ako ti backend vracia jeden záznam. Ak vracia { success: true, data: { ... } }, použi result.data
        // Ak vracia priamo ten objekt, daj tam len setOrg(result)
        setOrg(result.data || result); 
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchDetail();
  }, [id]);

  if (loading) return <div className="p-8 text-center text-gray-500">Načítavam detail...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
  if (!org) return null;

  return (
    <div className="max-w-3xl mx-auto p-6 mt-10 bg-white shadow-lg rounded-xl border">
      <div className="mb-6 flex justify-between items-start">
        <h1 className="text-4xl font-bold text-gray-800">{org.name}</h1>
        <Link to="/" className="text-blue-600 hover:underline">
          &larr; Späť na zoznam
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 text-lg">
        <div className="p-4 bg-gray-50 rounded">
          <p className="text-gray-500 text-sm uppercase font-bold">IČO</p>
          <p className="font-medium">{org.ico}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded">
          <p className="text-gray-500 text-sm uppercase font-bold">Právna forma</p>
          <p className="font-medium">{org.legal_form}</p>
        </div>
        
        {/* Tu môžeš pridávať ďalšie "dlaždice" s informáciami (adresa, zameranie...) */}
        {/* <div className="p-4 bg-gray-50 rounded col-span-2">
          <p className="text-gray-500 text-sm uppercase font-bold">Sídlo</p>
          <p className="font-medium">{org.hq_address}</p>
        </div> */}
      </div>
    </div>
  );
}