import logging

from celery import Celery

from core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("celery")


celery_app = Celery(
    'celery_app',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)


celery_app.conf.task_always_eager = False
celery_app.conf.result_backend_transport_options = {"visibility_timeout": 3600}
celery_app.conf.worker_hijack_root_logger = False
celery_app.conf.worker_pool = "solo"

celery_app.autodiscover_tasks(["celery_tasks"])


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        'send_notification_task': {'queue': 'default'}
    },
    task_default_queue='default',
)


@celery_app.task(bind=True)
def debug_task(self):
    print(f"Отладочная задача выполнена: {self.request!r}")
