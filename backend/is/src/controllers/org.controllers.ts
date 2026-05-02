/**
 * @file   org.controllers.ts
 * @brief  Request handlers for the organization resource.
 * @author Adam Kinzel (xkinzea00)
 *
 * Each exported function corresponds to one route in org.routes.ts.
 * Controllers are responsible only for parsing HTTP input, delegating to the
 * service layer, and formatting the HTTP response.
 */

import { Request, Response } from 'express';
import * as OrgService from '../services/org.service';

// Types

/** Prisma where-clause filter object (intentionally loose - validated by Prisma). */
type OrgFilters = Record<string, unknown>;


// Helpers 

/**
 * Build a Prisma filter object from the query parameters of a list request.
 *
 * IČO detection: a search term consisting solely of 1-8 digits is treated as
 * an IČO lookup (padded to 8 digits) rather than a full-text search.
 */
function buildFilters(query: Request['query']): OrgFilters {
    const filters: OrgFilters = {};

    if (query.ico) {
        filters.ico = query.ico as string;
    }

    if (query.legal_form) {
        filters.legal_form_code = query.legal_form as string;
    }

    if (query.name) {
        filters.name = { contains: query.name as string, mode: 'insensitive' };
    }

    if (query.size) {
        filters.size_category_code = query.size as string;
    }

    if (query.categories) {
        const categoryIds = (query.categories as string).split(',');
        filters.organization_category = {
            some: { category_id: { in: categoryIds } },
        };
    }

    if (query.search) {
        const searchTerm = (query.search as string).trim();
        const isIco = /^\d{1,8}$/.test(searchTerm);

        if (isIco) {
            // Pad to 8 digits to match the zero-padded storage format.
            filters.ico = searchTerm.padStart(8, '0');
        } else {
            filters.OR = [
                { name:       { contains: searchTerm, mode: 'insensitive' } },
                { hq_address: { contains: searchTerm, mode: 'insensitive' } },
            ];
        }
    }

    return filters;
}


// Handlers

/** Return a paginated, optionally filtered list of organizations. */
export const getAllOrganizations = async (req: Request, res: Response): Promise<void> => {
    try {
        const page     = req.query.page     ? parseInt(req.query.page     as string, 10) : 1;
        const pageSize = req.query.pageSize ? parseInt(req.query.pageSize as string, 10) : 24;
        const filters  = buildFilters(req.query);

        const result = await OrgService.getOrganizations(page, pageSize, filters);

        res.status(200).json({
            success: true,
            count:   result.organizations.length,
            data:    result.organizations,
            pagination: {
                page:       result.page,
                pageSize:   result.pageSize,
                total:      result.total,
                totalPages: result.totalPages,
            },
        });
    } catch {
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
};


/** Return the full detail of a single organization, including its branches. */
export const getOrganizationById = async (req: Request, res: Response): Promise<void> => {
    try {
        const org = await OrgService.getOrganizationById(req.params.id as string);

        if (!org) {
            res.status(404).json({ success: false, message: 'Organization not found' });
            return;
        }

        res.status(200).json({ success: true, data: org });
    } catch {
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
};


/** Delete an organization by ID. Returns 404 if it does not exist. */
export const deleteOrganization = async (req: Request, res: Response): Promise<void> => {
    try {
        const org = await OrgService.getOrganizationById(req.params.id as string);

        if (!org) {
            res.status(404).json({ success: false, message: 'Organization not found' });
            return;
        }

        await OrgService.deleteOrganization(req.params.id as string);
        res.status(200).json({ success: true, message: 'Organization was successfully deleted' });
    } catch (error) {
        console.error('Error in deleteOrganization:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
};


/** Return the metadata required to populate the filter controls of the UI. */
export const getFiltersMetadata = async (_req: Request, res: Response): Promise<void> => {
    try {
        const [categories, sizes, legalForms] = await Promise.all([
            OrgService.getCategories(),
            OrgService.getSizeCategories(),
            OrgService.getLegalForms(),
        ]);

        res.status(200).json({
            success: true,
            data: { categories, sizes, legalForms },
        });
    } catch {
        res.status(500).json({
            success: false,
            message: 'Internal server error while fetching filters',
        });
    }
};


/** Return organizations within a given radius of the supplied GPS coordinates. */
export const getNearbyOrganizations = async (req: Request, res: Response): Promise<void> => {
    try {
        const lat    = parseFloat(req.query.lat    as string);
        const lon    = parseFloat(req.query.lon    as string);
        const radius = req.query.radius ? parseFloat(req.query.radius as string) : 10;

        if (isNaN(lat) || isNaN(lon)) {
            res.status(400).json({
                success: false,
                message: 'Valid lat and lon query parameters are required',
            });
            return;
        }

        const orgs = await OrgService.getNearbyOrganizations(lat, lon, radius);
        res.status(200).json({ success: true, count: orgs.length, data: orgs });
    } catch {
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
};