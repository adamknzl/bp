import { Router } from 'express';
import { getAllOrganizations, getOrganizationById, getNearbyOrganizations, deleteOrganization, getFiltersMetadata } from '../controllers/org.controllers';

const router = Router();

router.get('/filters', getFiltersMetadata);
router.get('/nearby', getNearbyOrganizations);
router.get('/', getAllOrganizations);
router.get('/:id', getOrganizationById);

router.delete('/:id', deleteOrganization);

export default router;