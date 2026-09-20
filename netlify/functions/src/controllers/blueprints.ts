import { toInt } from '../utils/helpers';
import { Router, Response } from 'express';
import { query } from '../db';
import { AuthenticatedRequest, requireAuth } from '../middleware/auth';

const router = Router();

// ----------------------------------------------------------------------------
// GET /api/blueprints
// ----------------------------------------------------------------------------
router.get('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const result = await query(
      `SELECT id, title, description, vision, target_date, status, created_at, updated_at 
       FROM life_blueprints 
       WHERE user_id = $1 
       ORDER BY id DESC`,
      [req.user!.id]
    );
    return res.json({ blueprints: result.rows });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch blueprints' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/blueprints
// ----------------------------------------------------------------------------
router.post('/', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const { title, description, vision, target_date } = req.body || {};
    if (!title || !title.trim()) {
      return res.status(400).json({ detail: 'Blueprint title is required.' });
    }

    const ins = await query(
      `INSERT INTO life_blueprints (user_id, title, description, vision, target_date, status)
       VALUES ($1, $2, $3, $4, $5, 'active')
       RETURNING id, title, description, vision, target_date, status, created_at, updated_at`,
      [req.user!.id, title.trim(), description || '', vision || '', target_date || null]
    );

    return res.status(201).json({ blueprint: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to create blueprint' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/blueprints/active
// ----------------------------------------------------------------------------
router.get('/active', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const bpRes = await query(
      `SELECT id, title, description, vision, target_date, status, created_at, updated_at 
       FROM life_blueprints 
       WHERE user_id = $1 AND status = 'active' 
       ORDER BY id DESC LIMIT 1`,
      [req.user!.id]
    );

    if (bpRes.rows.length === 0) {
      return res.json({ blueprint: null, phases: [], areas: [], milestones: [] });
    }

    const blueprint = bpRes.rows[0];

    // Fetch areas
    const areasRes = await query(
      `SELECT id, name, description, icon, position FROM blueprint_areas WHERE blueprint_id = $1 ORDER BY position ASC`,
      [blueprint.id]
    );

    // Fetch phases
    const phasesRes = await query(
      `SELECT id, area_id, title, description, phase_number, status, position FROM blueprint_phases WHERE blueprint_id = $1 ORDER BY phase_number ASC`,
      [blueprint.id]
    );

    // Fetch milestones
    const msRes = await query(
      `SELECT id, phase_id, blueprint_id, title, description, target_date, completed, completed_at, position FROM blueprint_milestones WHERE blueprint_id = $1 ORDER BY position ASC`,
      [blueprint.id]
    );

    return res.json({
      blueprint,
      areas: areasRes.rows,
      phases: phasesRes.rows,
      milestones: msRes.rows,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch active blueprint' });
  }
});

// ----------------------------------------------------------------------------
// GET /api/blueprints/:id
// ----------------------------------------------------------------------------
router.get('/:id', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const bpId = toInt(req.params.id);
    const bpRes = await query(
      `SELECT id, title, description, vision, target_date, status, created_at, updated_at 
       FROM life_blueprints 
       WHERE id = $1 AND user_id = $2`,
      [bpId, req.user!.id]
    );

    if (bpRes.rows.length === 0) {
      return res.status(404).json({ detail: 'Blueprint not found' });
    }

    const blueprint = bpRes.rows[0];
    const phasesRes = await query(
      `SELECT id, area_id, title, description, phase_number, status, position FROM blueprint_phases WHERE blueprint_id = $1 ORDER BY phase_number ASC`,
      [blueprint.id]
    );
    const msRes = await query(
      `SELECT id, phase_id, blueprint_id, title, description, target_date, completed, completed_at, position FROM blueprint_milestones WHERE blueprint_id = $1 ORDER BY position ASC`,
      [blueprint.id]
    );

    return res.json({
      blueprint,
      phases: phasesRes.rows,
      milestones: msRes.rows,
    });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to fetch blueprint' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/blueprints/:id
// ----------------------------------------------------------------------------
router.patch('/:id', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const bpId = toInt(req.params.id);
    const { title, description, vision, target_date, status } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (title !== undefined) { updates.push(`title = $${pIdx++}`); params.push(title.trim()); }
    if (description !== undefined) { updates.push(`description = $${pIdx++}`); params.push(description.trim()); }
    if (vision !== undefined) { updates.push(`vision = $${pIdx++}`); params.push(vision.trim()); }
    if (target_date !== undefined) { updates.push(`target_date = $${pIdx++}`); params.push(target_date); }
    if (status !== undefined) { updates.push(`status = $${pIdx++}`); params.push(status); }

    if (updates.length === 0) {
      return res.json({ message: 'No updates provided' });
    }

    updates.push('updated_at = CURRENT_TIMESTAMP');
    params.push(bpId, req.user!.id);

    const sql = `UPDATE life_blueprints SET ${updates.join(', ')} WHERE id = $${pIdx++} AND user_id = $${pIdx} RETURNING id, title, description, vision, target_date, status, updated_at`;
    const resRow = await query(sql, params);

    return res.json({ blueprint: resRow.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update blueprint' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/blueprints/:id
// ----------------------------------------------------------------------------
router.delete('/:id', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const bpId = toInt(req.params.id);
    await query('DELETE FROM life_blueprints WHERE id = $1 AND user_id = $2', [bpId, req.user!.id]);
    return res.json({ message: 'Blueprint deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete blueprint' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/blueprints/:id/activate
// ----------------------------------------------------------------------------
router.post('/:id/activate', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const bpId = toInt(req.params.id);
    await query("UPDATE life_blueprints SET status = 'archived' WHERE user_id = $1", [req.user!.id]);
    await query("UPDATE life_blueprints SET status = 'active' WHERE id = $1 AND user_id = $2", [bpId, req.user!.id]);
    return res.json({ message: 'Blueprint activated successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to activate blueprint' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/blueprints/:id/phases
// ----------------------------------------------------------------------------
router.post('/:id/phases', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const bpId = toInt(req.params.id);
    const { title, description, phase_number, area_id } = req.body || {};
    const ins = await query(
      `INSERT INTO blueprint_phases (blueprint_id, area_id, title, description, phase_number, status)
       VALUES ($1, $2, $3, $4, $5, 'active')
       RETURNING *`,
      [bpId, area_id || null, title || 'New Phase', description || '', phase_number || 1]
    );
    return res.status(201).json({ phase: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to add phase' });
  }
});

// ----------------------------------------------------------------------------
// PATCH /api/blueprints/phases/:phaseId
// ----------------------------------------------------------------------------
router.patch('/phases/:phaseId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const phaseId = toInt(req.params.phaseId);
    const { title, description, status } = req.body || {};
    const updates: string[] = [];
    const params: any[] = [];
    let pIdx = 1;

    if (title !== undefined) { updates.push(`title = $${pIdx++}`); params.push(title.trim()); }
    if (description !== undefined) { updates.push(`description = $${pIdx++}`); params.push(description.trim()); }
    if (status !== undefined) { updates.push(`status = $${pIdx++}`); params.push(status); }

    if (updates.length === 0) return res.json({ message: 'No changes' });

    updates.push('updated_at = CURRENT_TIMESTAMP');
    params.push(phaseId);
    const sql = `UPDATE blueprint_phases SET ${updates.join(', ')} WHERE id = $${pIdx} RETURNING *`;
    const result = await query(sql, params);

    return res.json({ phase: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to update phase' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/blueprints/phases/:phaseId
// ----------------------------------------------------------------------------
router.delete('/phases/:phaseId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const phaseId = toInt(req.params.phaseId);
    await query('DELETE FROM blueprint_phases WHERE id = $1', [phaseId]);
    return res.json({ message: 'Phase deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete phase' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/blueprints/phases/:phaseId/milestones
// ----------------------------------------------------------------------------
router.post('/phases/:phaseId/milestones', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const phaseId = toInt(req.params.phaseId);
    const { title, description, target_date, blueprint_id } = req.body || {};
    const ins = await query(
      `INSERT INTO blueprint_milestones (phase_id, blueprint_id, title, description, target_date, completed)
       VALUES ($1, $2, $3, $4, $5, 0)
       RETURNING *`,
      [phaseId, blueprint_id, title || 'New Milestone', description || '', target_date || null]
    );
    return res.status(201).json({ milestone: ins.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to add milestone' });
  }
});

// ----------------------------------------------------------------------------
// DELETE /api/blueprints/milestones/:milestoneId
// ----------------------------------------------------------------------------
router.delete('/milestones/:milestoneId', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const msId = toInt(req.params.milestoneId);
    await query('DELETE FROM blueprint_milestones WHERE id = $1', [msId]);
    return res.json({ message: 'Milestone deleted successfully' });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to delete milestone' });
  }
});

// ----------------------------------------------------------------------------
// POST /api/blueprints/milestones/:milestoneId/toggle
// ----------------------------------------------------------------------------
router.post('/milestones/:milestoneId/toggle', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const msId = toInt(req.params.milestoneId);
    const cur = await query('SELECT completed FROM blueprint_milestones WHERE id = $1', [msId]);
    if (cur.rows.length === 0) return res.status(404).json({ detail: 'Milestone not found' });

    const newCompleted = cur.rows[0].completed ? 0 : 1;
    const completedAt = newCompleted ? new Date().toISOString() : null;

    const result = await query(
      `UPDATE blueprint_milestones 
       SET completed = $1, completed_at = $2, updated_at = CURRENT_TIMESTAMP 
       WHERE id = $3 
       RETURNING *`,
      [newCompleted, completedAt, msId]
    );

    return res.json({ milestone: result.rows[0] });
  } catch (err: any) {
    return res.status(500).json({ detail: err?.message || 'Failed to toggle milestone' });
  }
});

export default router;
