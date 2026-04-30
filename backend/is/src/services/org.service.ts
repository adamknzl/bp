import 'dotenv/config';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '@prisma/client';

const pool = new Pool({ 
    connectionString: process.env.DATABASE_URL 
});

const adapter = new PrismaPg(pool);

const prisma = new PrismaClient({ adapter });

export const getLegalForms = async () => {
    try {
        return await prisma.legal_form.findMany({
            orderBy: { name: 'asc' }
        });
    } catch (error) {
        console.error("Database query failed:", error);
        throw new Error("Failed to fetch legal forms");
    }
};

export const getOrganizations = async (
    page: number = 1,
    pageSize: number = 24,
    filters: any = {}
) => {
    try {
        const skip = (page - 1) * pageSize;

        const [organizations, total] = await prisma.$transaction([
            prisma.organization.findMany({
                include: {
                    organization_category: {
                        include: {
                            category: true
                        }
                    },
                    legal_form_rel: true,
                    size_category_rel: true
                },
                where: filters,
                skip,
                take: pageSize,
                orderBy: { name: 'asc' }
            }),
            prisma.organization.count({ where: filters })
        ]);

        return {
            organizations,
            total,
            page,
            pageSize,
            totalPages: Math.ceil(total / pageSize)
        };
    } catch (error) {
        console.error("Database query failed:", error);
        throw new Error("Failed to fetch organizations");
    }
};

export const getOrganizationById = async (id: string) => {
    try {
        const organization = await prisma.organization.findUnique({
            where: {
                organization_id: id
            },
            include: {
                organization_category: {
                    include: { category: true }
                },
                branches: true,
                other_organization: true,
                legal_form_rel: true,
                size_category_rel: true
            }
        });
        return organization;
    } catch (error) {
        console.error(`Database query failed for ID ${id}:`, error);
        throw new Error("Failed to fetch organization detail");
    }
}

export const deleteOrganization = async (id: string) => {
    try {
        const organization = await prisma.organization.delete({
            where: {
                organization_id: id
            }
        });
        return organization;
    } catch (error) {
        console.error(`Database query failed for ID ${id}:`, error);
        throw new Error("Failed to delete organization");
    }
};

export const getCategories = async () => {
    try {
        return await prisma.category.findMany({
            orderBy: { name: 'asc' }
        });
    } catch (error) {
        console.error("Database query failed:", error);
        throw new Error("Failed to fetch categories");
    }
};

export const getSizeCategories = async () => {
    try {
        return await prisma.size_category.findMany({
            orderBy: { min_emp: 'asc' }
        });
    } catch (error) {
        console.error("Database query failed:", error);
        throw new Error("Failed to fetch size categories");
    }
};

export const getNearbyOrganizations = async (
    lat: number,
    lon: number,
    radiusKm: number = 10,
    limit: number = 50
) => {
    try {
        const organizations = await prisma.$queryRaw<any[]>`
            SELECT 
                o.*,
                (
                    6371 * acos(
                        cos(radians(${lat})) * cos(radians(o.lat)) *
                        cos(radians(o.lon) - radians(${lon})) +
                        sin(radians(${lat})) * sin(radians(o.lat))
                    )
                ) AS distance_km
            FROM organization o
            WHERE o.lat IS NOT NULL 
              AND o.lon IS NOT NULL
              AND (
                    6371 * acos(
                        cos(radians(${lat})) * cos(radians(o.lat)) *
                        cos(radians(o.lon) - radians(${lon})) +
                        sin(radians(${lat})) * sin(radians(o.lat))
                    )
                ) <= ${radiusKm}
            ORDER BY distance_km ASC
            LIMIT ${limit}
        `;

        const orgIds = organizations.map(o => o.organization_id);
        const orgsWithRelations = await prisma.organization.findMany({
            where: { organization_id: { in: orgIds } },
            include: {
                organization_category: { include: { category: true } },
                legal_form_rel: true,
                size_category_rel: true
            }
        });

        const distanceMap = new Map(
            organizations.map(o => [o.organization_id, o.distance_km])
        );

        return orgsWithRelations
            .map(o => ({ ...o, distance_km: distanceMap.get(o.organization_id) }))
            .sort((a, b) => (a.distance_km ?? 0) - (b.distance_km ?? 0));
    } catch (error) {
        console.error("Database query failed:", error);
        throw new Error("Failed to fetch nearby organizations");
    }
};