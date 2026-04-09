export interface Category {
  category_id: string;
  name: string;
}

export interface SizeCategory {
  cat_id: string;
  label: string;
}

export interface Branch {
  branch_id: string;
  city: string | null;
  street: string | null;
  email: string | null;
  tel_num: string | null;
  lat: number | null;
  lon: number | null;
}

export interface ChildOrganization {
  organization_id: string;
  name: string;
  hq_address: string | null;
  lat: number | null;
  lon: number | null;
}

export interface Organization {
  organization_id: string;
  name: string;
  ico: string;
  legal_form: string | null;
  hq_address: string | null;
  description: string | null;
  organization_category?: { category: Category }[];
}

export interface OrganizationDetail extends Organization {
  web_url: string | null;
  emails: string[];
  tel_numbers: string[];
  lat: number | null;
  lon: number | null;
  branches?: Branch[];
  other_organization?: ChildOrganization[];
}

export interface MapLocation {
  id: string;
  title: string;
  address: string;
  isHQ: boolean;
  lat?: number | null;
  lon?: number | null;
}