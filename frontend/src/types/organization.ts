/**
 * @file  organization.ts
 * @brief TypeScript interfaces that mirror the API response shapes for the
 *        organization resource and its related entities.
 * @author Adam Kinzel (xkinzea00)
 */

/** Thematic category of an organization. */
export interface Category {
  category_id: string;
  name:        string;
}

/** Physical branch of an organization. */
export interface Branch {
  branch_id: string;
  city:      string | null;
  street:    string | null;
  email:     string | null;
  tel_num:   string | null;
  lat:       number | null;
  lon:       number | null;
}

/**
 * Child organization in the parent-branch hierarchy.
 * Carries only the fields required to render the branch list and map.
 */
export interface ChildOrganization {
  organization_id: string;
  name:            string;
  hq_address:      string | null;
  lat:             number | null;
  lon:             number | null;
}

/** Legal form codebook entry (e.g. "Spolek"). */
export interface LegalForm {
  code: string;
  name: string;
}

/** Size category codebook entry (e.g. "1 - 5 zaměstnanců"). */
export interface SizeCategory {
  code:    string;
  label:   string;
  min_emp: number | null;
  max_emp: number | null;
}

/** Organization as returned by the list endpoint. */
export interface Organization {
  organization_id:       string;
  name:                  string;
  ico:                   string;
  legal_form_code:       string | null;
  size_category_code:    string | null;
  hq_address:            string | null;
  description:           string | null;
  organization_category?: { category: Category }[];
  legal_form_rel?:        LegalForm | null;
  size_category_rel?:     SizeCategory | null;
}

/** Full organization detail as returned by the single-resource endpoint. */
export interface OrganizationDetail extends Organization {
  web_url:            string | null;
  emails:             string[];
  tel_numbers:        string[];
  lat:                number | null;
  lon:                number | null;
  branches?:          Branch[];
  other_organization?: ChildOrganization[];
}

/** Organization enriched with a computed distance from the user's position. */
export interface NearbyOrganization extends Organization {
  distance_km: number;
}

/** Marker data used to render pins on the Leaflet map in the detail view. */
export interface MapLocation {
  id:      string;
  title:   string;
  address: string;
  isHQ:    boolean;
  lat?:    number | null;
  lon?:    number | null;
}