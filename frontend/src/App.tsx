import { useEffect, useState } from 'react';

interface Organization {
  organization_id: string;
  name: string;
  ico: string;
  legal_form: string;
}

function App() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const response = await fetch('http://localhost:3000/api/organizations');
        if (!response.ok) throw new Error("Chyba pri sťahovaní dát");
        
        const result = await response.json();
        setOrganizations(result.data);
      } catch (err) {
        setError("Nepodarilo sa načítať organizácie.");
      } finally {
        setLoading(false);
      }
    };

    fetchOrgs();
  }, []);

  if (loading) return <div>Loading data...</div>;
  if (error) return <div style={{ color: 'red' }}>{error}</div>;

  return (
    <div>      
      <ul>
        {organizations.map((org) => (
          <li key={org.organization_id} style={{ marginBottom: '10px' }}>
            <strong>{org.name}</strong> (IČO: {org.ico}) <br />
            <small>{org.legal_form}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;