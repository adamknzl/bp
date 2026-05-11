/**
 * @file   org.service.ts
 * @brief  Database access layer for the organization resource.
 * @author Adam Kinzel (xkinzea00)
 *
 * All Prisma queries are centralised here. Controllers delegate to these
 * functions and never interact with the database client directly.
 * The Prisma client is initialised once at module level using the PrismaPg
 * adapter backed by a pg connection pool, enabling connection reusing.
 */

import 'dotenv/config';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '@prisma/client';

const pool = new Pool({ 
    connectionString: process.env.DATABASE_URL 
});

const adapter = new PrismaPg(pool);

const prisma = new PrismaClient({ adapter });

/** Return all legal form codebook entries ordered alphabetically by name. */
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

/**
 * Return a paginated, optionally filtered list of organizations.
 *
 * Each record includes its thematic categories, legal form, and size category
 * via Prisma's nested include. The filters argument is a raw Prisma where-clause
 * object constructed by the controller layer.
 */
export const getOrganizations = async (
    page: number = 1,
    pageSize: number = 24,
    filters: any = {}
) => {
    try {
        const skip = (page - 1) * pageSize;

        // Execute count and data queries concurrently to minimize latency
        const [organizations, total] = await Promise.all([
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

/**
 * Return the full detail of a single organization by its UUID.
 *
 * Includes thematic categories, physical branches, child organizations
 * in the parent-branch hierarchy, and both codebook relations.
 * Returns null when no record matches the given ID.
 */
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

/** Permanently delete an organization record by its UUID. */
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

/** Return all thematic category entries ordered alphabetically by name. */
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

/**
 * Return all size category codebook entries ordered by minimum employee count.
 * Null min_emp values (the "Neuvedeno" entry) sort to the end.
 */
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

/**
 * Return organizations within a given radius of the supplied GPS coordinates.
 *
 * Distance is computed on the database side using the Haversine formula,
 * which calculates the great-circle (straight-line) distance between two
 * points on the Earth's surface given their latitude and longitude.
 *
 * Because Prisma does not natively support computed columns in ORDER BY,
 * the query is executed in two steps:
 * 1. A raw SQL query computes distances and returns matching organization IDs.
 * 2. A standard Prisma query fetches the full records with relational data
 *    for those IDs, after which distances are re-attached and results re-sorted.
 */
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

        // Re-attach computed distances and sort ascending by distance.
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