# API contract

GET    /api/problems
POST   /api/jobs
GET    /api/jobs
GET    /api/jobs/{id}
PATCH  /api/jobs/{id}
POST   /api/jobs/{id}/pause
POST   /api/jobs/{id}/resume
POST   /api/jobs/{id}/cancel
POST   /api/jobs/{id}/fork
GET    /api/jobs/{id}/events     (SSE)
GET    /api/jobs/{id}/units
POST   /api/experiments
GET    /api/experiments
GET    /api/experiments/{id}
GET    /api/experiments/{id}/events  (SSE)
GET    /api/artifacts/{id}/url
GET    /api/artifacts?job_id=&kind=
GET    /health
