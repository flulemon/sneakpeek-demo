import argparse
import random
from uuid import uuid4

from sneakpeek.logging import configure_logging
from sneakpeek.middleware.parser import ParserMiddleware
from sneakpeek.middleware.rate_limiter_middleware import (
    RateLimiterMiddleware,
    RateLimiterMiddlewareConfig,
)
from sneakpeek.middleware.requests_logging_middleware import RequestsLoggingMiddleware
from sneakpeek.queue.in_memory_storage import InMemoryQueueStorage
from sneakpeek.queue.model import TaskPriority
from sneakpeek.scheduler.in_memory_lease_storage import InMemoryLeaseStorage
from sneakpeek.scheduler.model import TaskSchedule
from sneakpeek.scraper.in_memory_storage import InMemoryScraperStorage
from sneakpeek.scraper.model import Scraper, ScraperConfig, ScraperStorageABC
from sneakpeek.server import SneakpeekServer
from sneakpeek.session_loggers.base import SessionLogger
from sneakpeek.session_loggers.file_logger import FileLoggerHandler

from demo.demo_scraper import DemoScraper

parser = argparse.ArgumentParser(prog="Sneakpeek Demo")

parser.add_argument(
    "-u",
    "--url",
    action="append",
    dest="urls",
    help="URLs to create demo scrapers for",
    default=[
        "https://google.com",
        "https://www.docker.com/",
    ],
)
parser.add_argument(
    "--read-only",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Whether to allow modifying list of scrapers or not",
)


def get_scrapers(urls: list[str]) -> list[Scraper]:
    return [
        Scraper(
            id=str(uuid4()),
            name=f"Demo Scraper ({url})",
            schedule=TaskSchedule.EVERY_MINUTE,
            handler=DemoScraper().name,
            config=ScraperConfig(params={"start_url": url, "max_pages": 5}),
            schedule_priority=random.choice(
                [
                    TaskPriority.HIGH,
                    TaskPriority.UTMOST,
                    TaskPriority.NORMAL,
                ]
            ),
        )
        for url in urls
    ]


def get_scraper_storage(urls: list[str], is_read_only: bool) -> ScraperStorageABC:
    return InMemoryScraperStorage(
        initial_scrapers=get_scrapers(urls),
        is_read_only=is_read_only,
    )


def get_server(
    urls: list[str],
    is_read_only: bool,
    session_logger: SessionLogger,
) -> SneakpeekServer:
    return SneakpeekServer.create(
        handlers=[DemoScraper()],
        scraper_storage=get_scraper_storage(urls, is_read_only),
        queue_storage=InMemoryQueueStorage(),
        lease_storage=InMemoryLeaseStorage(),
        middlewares=[
            RequestsLoggingMiddleware(),
            RateLimiterMiddleware(RateLimiterMiddlewareConfig(max_rpm=60)),
            ParserMiddleware(),
        ],
        add_dynamic_scraper_handler=True,
        session_logger_handler=session_logger,
    )


def main():
    session_logger = FileLoggerHandler(f"logs/{uuid4()}/")
    args = parser.parse_args()
    server = get_server(args.urls, args.read_only, session_logger)
    configure_logging(session_logger_handler=session_logger)
    server.serve()


if __name__ == "__main__":
    main()
