/**
 * @file   org.routes.ts
 * @brief  Route definitions for the /api/organizations resource.
 * @author Adam Kinzel (xkinzea00)
 *
 * Route ordering is intentional - specific static paths (/filters, /nearby)
 * must be declared before the dynamic /:id segment, otherwise Express would
 * view them as ID parameters.
 */

import { Router } from 'express';
import {
    getAllOrganizations,
    getOrganizationById,
    getNearbyOrganizations,
    deleteOrganization,
    getFiltersMetadata,
} from '../controllers/org.controllers';

const router = Router();

// Static routes (must precede /:id)
router.get('/filters', getFiltersMetadata);
router.get('/nearby',  getNearbyOrganizations);

// Collection and resource routes
router.get('/',    getAllOrganizations);
router.get('/:id', getOrganizationById);

router.delete('/:id', deleteOrganization);

export default router;