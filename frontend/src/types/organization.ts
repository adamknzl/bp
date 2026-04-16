export interface Category {
  category_id: string;
  name: string;
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

export interface LegalForm {
  code: string;
  name: string;
}

export interface SizeCategory {
  code: string;
  label: string;
  min_emp: number | null;
  max_emp: number | null;
}

export interface Organization {
  organization_id: string;
  name: string;
  ico: string;
  legal_form_code: string | null;
  size_category_code: string | null;
  hq_address: string | null;
  description: string | null;
  organization_category?: { category: Category }[];
  legal_form_rel?: LegalForm | null;
  size_category_rel?: SizeCategory | null;
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