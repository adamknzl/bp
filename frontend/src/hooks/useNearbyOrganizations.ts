import { useState } from 'react';
import { API_BASE_URL } from '../config/api';
import type { Organization } from '../types/organization';

export function useNearbyOrganizations() {
    const [organizations, setOrganizations] = useState<Organization[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const findNearby = async (radiusKm: number = 10) => {
        setLoading(true);
        setError(null);

        if (!navigator.geolocation) {
            setError("Váš prehliadač nepodporuje geolokáciu.");
            setLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async position => {
                const { latitude, longitude } = position.coords;
                try {
                    const response = await fetch(
                        `${API_BASE_URL}/organizations/nearby?lat=${latitude}&lon=${longitude}&radius=${radiusKm}`
                    );
                    if (!response.ok) throw new Error('Failed to fetch nearby organizations');
                    const result = await response.json();
                    setOrganizations(result.data);
                } catch {
                    setError("Nepodarilo sa načítať organizácie v okolí.");
                } finally {
                    setLoading(false);
                }
            },
            err => {
                if (err.code === err.PERMISSION_DENIED) {
                    setError("Pre vyhľadanie organizácií v okolí je potrebné povoliť prístup k polohe.");
                } else {
                    setError("Nepodarilo sa získať vašu polohu.");
                }
                setLoading(false);
            }
        );
    };

    return { organizations, loading, error, findNearby };
}