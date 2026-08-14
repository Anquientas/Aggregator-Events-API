from prometheus_client import Counter, Gauge, Histogram

# --- HTTP-запросы (собираются в MetricsMiddleware) ---

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Общее количество HTTP-запросов",
    labelnames=("method", "endpoint", "status"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Время обработки HTTP-запросов",
    labelnames=("method", "endpoint"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# --- Запросы к Events Provider API (собираются в EventsProviderClient) ---

EVENTS_PROVIDER_REQUESTS_TOTAL = Counter(
    "events_provider_requests_total",
    "Количество запросов к Events Provider API",
    labelnames=("endpoint", "status"),
)
EVENTS_PROVIDER_REQUEST_DURATION_SECONDS = Histogram(
    "events_provider_request_duration_seconds",
    "Время ответа Events Provider API",
    labelnames=("endpoint",),
)

# --- Бизнес-метрики (Gauge, заполняются из БД прямо в эндпоинте /metrics) ---

EVENTS_TOTAL = Gauge(
    "events_total",
    "Текущее количество событий в базе данных",
)
TICKETS_CREATED_TOTAL = Gauge(
    "tickets_created_total",
    "Общее количество созданных билетов в базе данных",
)
TICKETS_CANCELLED_TOTAL = Gauge(
    "tickets_cancelled_total",
    "Общее количество отменённых билетов в базе данных",
)

# --- Кэш свободных мест (собираются в GetSeatsUsecase) ---

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Попадания в локальный кэш свободных мест",
)
CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Промахи локального кэша свободных мест",
)
