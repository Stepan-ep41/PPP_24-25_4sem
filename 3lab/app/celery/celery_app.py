from app.core.config import Config
from celery import Celery

# Канал для общения с коиентом
REDIS_BROKER = f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/0'
# Канал где выполняются тяжелые процессы
REDIS_BACKEND = f'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/1'


celery_app = Celery(
    '3lab',
    broker=REDIS_BROKER,
    backend=REDIS_BACKEND,
)


# Определяем формат принимаемых и передаваемых данных
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,
)


# Передаем все долгие процессы, которые выполняются на celery + redis
celery_app.autodiscover_tasks(['app.celery.tasks'])