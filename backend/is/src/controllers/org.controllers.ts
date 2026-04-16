import { Request, Response } from 'express';
import * as OrgService from '../services/org.service';

export const getAllOrganizations = async (req: Request, res: Response): Promise<void> => {
    try {
        const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 50;
        const filters: any = {};

        if (req.query.ico) {
            filters.ico = req.query.ico as string;
        }

        if (req.query.legal_form) {
            filters.legal_form_code = req.query.legal_form as string;
        }

        if (req.query.name) {
            filters.name = {
                contains: req.query.name as string,
                mode: 'insensitive'
            };
        }

        if (req.query.size) {
            filters.size_category_code = req.query.size as string;
        }

        if (req.query.categories) {
            const categoryIds = (req.query.categories as string).split(',');
            
            filters.organization_category = {
                some: {
                    category_id: {
                        in: categoryIds
                    }
                }
            };
        }

        if (req.query.search) {
            const searchTerm = req.query.search as string;
            filters.OR = [
                { name: { contains: searchTerm, mode: 'insensitive' } },
                { hq_address: { contains: searchTerm, mode: 'insensitive' } }
            ];
        }

        const orgs = await OrgService.getOrganizations(limit, filters);

        res.status(200).json({
            success: true,
            count: orgs.length,
            data: orgs
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: "Internal server error"
        });
    }
};

export const getOrganizationById = async (req: Request, res: Response): Promise<void> => {
    try {
        const id = req.params.id as string;
        const org = await OrgService.getOrganizationById(id);

        if (!org) {
            res.status(404).json({
                success: false,
                message: "Organization not found"
            });
            return;
        }

        res.status(200).json({
            success: true,
            data: org
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: "Internal server error"
        });
    }
};

export const deleteOrganization = async (req: Request, res: Response): Promise<void> => {
    try {
        const id = req.params.id as string;
        const org = await OrgService.getOrganizationById(id);

        if(!org) {
            res.status(404).json({
                success: false,
                message: "Organization not found"
            });
            return;
        }

        await OrgService.deleteOrganization(id);

        res.status(200).json({
            succcess: true,
            message: "Organization was successfully deleted"
        });
    } catch (error) {
        console.error("Error in deleteOrganization:", error);
        res.status(500).json({
            success: false,
            message: "Internal server error"
        });
    }
}

export const getFiltersMetadata = async (req: Request, res: Response): Promise<void> => {
    try {
        const categories = await OrgService.getCategories();
        const sizes = await OrgService.getSizeCategories();
        const legalForms = await OrgService.getLegalForms();

        res.status(200).json({
            success: true,
            data: {
                categories,
                sizes,
                legalForms
            }
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: "Internal server error while fetching filters"
        });
    }
};