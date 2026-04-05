import 'dotenv/config';
import { Pool } from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from '@prisma/client';

const pool = new Pool({ 
    connectionString: process.env.DATABASE_URL 
});

const adapter = new PrismaPg(pool);

const prisma = new PrismaClient({ adapter });

export const getOrganizations = async (limit: number = 50, filters: any = {}) => {
    try {
        const organizations = await prisma.organization.findMany({
            where: filters,
            take: limit,
            orderBy: { name: 'asc' }
        });
        return organizations;
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