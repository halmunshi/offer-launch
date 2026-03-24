from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="generate_funnel_task")
def generate_funnel_task(self, workflow_run_id: str) -> None:
    _ = (self, workflow_run_id)
