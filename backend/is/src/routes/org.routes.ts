import { Router } from 'express';
import { getAllOrganizations, getOrganizationById, deleteOrganization, getFiltersMetadata } from '../controllers/org.controllers';

const router = Router();

router.get('/filters', getFiltersMetadata);

router.get('/', getAllOrganizations);
router.get('/:id', getOrganizationById);

router.delete('/:id', deleteOrganization);

export default router;