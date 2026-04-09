import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

import { useOrganization } from '../hooks/useOrganization';
import { getCategoryColor } from '../constants/categories';
import type { MapLocation } from '../types/organization';

// ─── Leaflet default icon fix ─────────────────────────────────────────────────

L.Marker.prototype.options.icon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// ─── Constants ────────────────────────────────────────────────────────────────

const CONTACTS_LIMIT = 2;

// ─── Sub-components ──────────────────────────────────────────────────────────

function FitBounds({ markers }: { markers: MapLocation[] }) {
  const map = useMap();

  useEffect(() => {
    if (markers.length > 0) {
      // Leaflet expects [lat, lng] — note: fixed from original [lon, lat] bug
      const bounds = L.latLngBounds(markers.map(m => [m.lat!, m.lon!]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
    }
  }, [markers, map]);

  return null;
}

interface ContactListProps {
  items: string[];
  href: (item: string) => string;
  showAll: boolean;
  onToggle: () => void;
  expandLabel: (remaining: number) => string;
  collapseLabel: string;
  emptyLabel?: string;
}

function ContactList({
  items,
  href,
  showAll,
  onToggle,
  expandLabel,
  collapseLabel,
  emptyLabel = 'Neuvedené',
}: ContactListProps) {
  if (!items || items.length === 0) {
    return <span className="text-gray-500 font-normal italic">{emptyLabel}</span>;
  }

  const visible = showAll ? items : items.slice(0, CONTACTS_LIMIT);

  return (
    <>
      {visible.map((item, idx) => (
        <a key={idx} href={href(item)} className="block hover:underline">
          {item}
        </a>
      ))}
      {items.length > CONTACTS_LIMIT && (
        <button
          onClick={onToggle}
          className="text-xs text-gray-500 hover:text-[#005A92] font-bold mt-2 outline-none"
        >
          {showAll ? collapseLabel : expandLabel(items.length - CONTACTS_LIMIT)}
        </button>
      )}
    </>
  );
}

// ─── Page component ───────────────────────────────────────────────────────────

export default function OrganizationDetail() {
  const { id } = useParams<{ id: string }>();
  const { org, loading, error } = useOrganization(id);

  const [showAllEmails, setShowAllEmails] = useState(false);
  const [showAllPhones, setShowAllPhones] = useState(false);

  if (loading) {
    return <div className="p-12 text-center text-gray-500 font-medium">Načítavam detail...</div>;
  }
  if (error) {
    return <div className="p-12 text-center text-red-500 font-bold">{error}</div>;
  }
  if (!org) return null;

  // ─── Build map locations ─────────────────────────────────────────────────

  const locations: MapLocation[] = [];

  const hasGeoData = org.lat != null && org.lon != null;
  const hasChildren = org.other_organization && org.other_organization.length > 0;

  if (hasGeoData || hasChildren) {
    locations.push({
      id: org.organization_id,
      title: 'Centrála organizácie',
      address: org.hq_address ?? 'Adresa centrály neuvedená',
      isHQ: true,
      lat: org.lat,
      lon: org.lon,
    });

    org.other_organization?.forEach(child => {
      if (child.organization_id !== org.organization_id) {
        locations.push({
          id: child.organization_id,
          title: child.name,
          address: child.hq_address ?? 'Adresa neuvedená',
          isHQ: false,
          lat: child.lat,
          lon: child.lon,
        });
      }
    });
  }

  // Only markers that have valid coordinates
  const mapMarkers = locations.filter(l => l.lat != null && l.lon != null);

  return (
    <div className="min-h-screen bg-[#F8F9FA] pb-20">
      <div className="max-w-[1200px] mx-auto px-8 pt-10">

        {/* Back navigation */}
        <Link
          to="/"
          className="text-gray-500 hover:text-[#005A92] transition text-sm flex items-center gap-2 mb-6"
        >
          <span>&larr;</span> back to search results
        </Link>

        {/* Header */}
        <div className="mb-10">
          <h1 className="text-4xl font-extrabold text-[#005A92] font-['Manrope',sans-serif] mb-2">
            {org.name}
          </h1>
          <h3 className="text-md text-gray-700 mb-4">{org.legal_form}</h3>
          <div className="flex gap-2 flex-wrap">
            {org.organization_category?.map(({ category }) => (
              <span
                key={category.category_id}
                className={`px-3 py-1.5 text-xs font-bold rounded-full uppercase tracking-wider ${getCategoryColor(category.name)}`}
              >
                {category.name}
              </span>
            ))}
          </div>
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">

          {/* Left column — Description & Branches */}
          <div className="lg:col-span-2 space-y-12">

            <section>
              <h2 className="text-2xl font-bold text-[#005A92] font-['Manrope',sans-serif] mb-4">
                Description
              </h2>
              <div className="text-gray-700 leading-relaxed text-base">
                {org.description ? (
                  <p>{org.description}</p>
                ) : (
                  <p className="italic opacity-60">
                    Organizácia zatiaľ neposkytla bližší popis svojej činnosti.
                  </p>
                )}
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-[#005A92] font-['Manrope',sans-serif] mb-6">
                Branches
              </h2>

              {/* Map */}
              <div className="w-full h-80 bg-gray-200 rounded-xl mb-6 overflow-hidden shadow-sm border border-gray-100 z-0">
                {mapMarkers.length > 0 ? (
                  <MapContainer
                    // Fixed: Leaflet expects [lat, lon], not [lon, lat]
                    center={[mapMarkers[0].lat!, mapMarkers[0].lon!]}
                    zoom={12}
                    scrollWheelZoom={false}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    <FitBounds markers={mapMarkers} />
                    {mapMarkers.map(loc => (
                      <Marker key={loc.id} position={[loc.lat!, loc.lon!]}>
                        <Popup>
                          <strong>{loc.title}</strong>
                          <br />
                          {loc.address}
                        </Popup>
                      </Marker>
                    ))}
                  </MapContainer>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-500 bg-gray-50">
                    Pre túto organizáciu zatiaľ nemáme presné GPS súradnice.
                  </div>
                )}
              </div>

              {/* Branch list */}
              <div className="space-y-4">
                {locations.length > 0 ? (
                  locations.map(loc => (
                    <div
                      key={loc.id}
                      className="bg-white p-5 rounded-xl flex items-center gap-5 shadow-sm border border-gray-100"
                    >
                      <div
                        className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                          loc.isHQ ? 'bg-[#005A92] text-white' : 'bg-[#E2F5EA] text-[#2D6A4F]'
                        }`}
                      >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                      </div>
                      <div className="flex-grow">
                        <h4 className="text-lg font-bold text-gray-900">{loc.title}</h4>
                        <p className="text-gray-500 text-sm">{loc.address}</p>
                      </div>
                      <div
                        className={`hidden sm:block text-xs font-bold uppercase tracking-wider ${
                          loc.isHQ ? 'text-[#005A92]' : 'text-gray-400'
                        }`}
                      >
                        {loc.isHQ ? 'Hlavní ústředí' : 'Pobočka'}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 italic p-4 bg-gray-50 rounded-lg">
                    Táto organizácia zatiaľ nemá evidované žiadne ďalšie pobočky.
                  </p>
                )}
              </div>
            </section>
          </div>

          {/* Right column — Contact info */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 sticky top-24">
              <h3 className="text-2xl font-bold text-[#005A92] font-['Manrope',sans-serif] border-b border-gray-100 pb-4 mb-6">
                Contact info
              </h3>

              <div className="space-y-8">

                {/* E-mails */}
                <div>
                  <div className="flex items-center gap-2 text-gray-400 mb-3 uppercase tracking-wider text-xs font-bold">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    E-mail addresses
                  </div>
                  <div className="space-y-2 ml-6 text-sm font-medium text-[#005A92]">
                    <ContactList
                      items={org.emails}
                      href={email => `mailto:${email}`}
                      showAll={showAllEmails}
                      onToggle={() => setShowAllEmails(v => !v)}
                      expandLabel={n => `+ Ďalšie e-maily (${n})`}
                      collapseLabel="- Zobraziť menej"
                    />
                  </div>
                </div>

                {/* Phones */}
                <div>
                  <div className="flex items-center gap-2 text-gray-400 mb-3 uppercase tracking-wider text-xs font-bold">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    Telephone contacts
                  </div>
                  <div className="space-y-2 ml-6 text-sm font-medium text-gray-800">
                    <ContactList
                      items={org.tel_numbers}
                      href={phone => `tel:${phone}`}
                      showAll={showAllPhones}
                      onToggle={() => setShowAllPhones(v => !v)}
                      expandLabel={n => `+ Ďalšie čísla (${n})`}
                      collapseLabel="- Zobraziť menej"
                    />
                  </div>
                </div>

                {/* Website */}
                <div>
                  <div className="flex items-center gap-2 text-gray-400 mb-3 uppercase tracking-wider text-xs font-bold">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                    Website
                  </div>
                  <div className="space-y-2 ml-6 text-sm font-medium text-[#005A92]">
                    {org.web_url ? (
                      <a
                        href={org.web_url.startsWith('http') ? org.web_url : `https://${org.web_url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block hover:underline"
                      >
                        {org.web_url.replace(/^https?:\/\//, '')}
                      </a>
                    ) : (
                      <span className="text-gray-500 font-normal italic">Neuvedené</span>
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