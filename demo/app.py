import argparse
import random

from sneakpeek.lib.models import Scraper, ScraperJobPriority, ScraperSchedule
from sneakpeek.lib.storage.base import ScrapersStorage
from sneakpeek.lib.storage.in_memory_storage import (
    InMemoryLeaseStorage,
    InMemoryScraperJobsStorage,
    InMemoryScrapersStorage,
)
from sneakpeek.logging import configure_logging
from sneakpeek.plugins.rate_limiter_plugin import (
    RateLimiterPlugin,
    RateLimiterPluginConfig,
)
from sneakpeek.plugins.requests_logging_plugin import RequestsLoggingPlugin
from sneakpeek.plugins.robots_txt_plugin import RobotsTxtPlugin
from sneakpeek.plugins.user_agent_injecter_plugin import (
    UserAgentInjecterPlugin,
    UserAgentInjecterPluginConfig,
)
from sneakpeek.scraper_config import ScraperConfig
from sneakpeek.server import SneakpeekServer

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
        "https://www.blogger.com",
        "https://youtube.com",
        "https://www.ycombinator.com/",
    ],
)
parser.add_argument(
    "--read-only",
    default=True,
    action=argparse.BooleanOptionalAction,
    help="Whether to allow modifying list of scrapers or not",
)


def get_scrapers(urls: list[str]) -> list[Scraper]:
    return [
        Scraper(
            id=id,
            name=f"Demo Scraper ({url})",
            schedule=ScraperSchedule.EVERY_MINUTE,
            handler=DemoScraper().name,
            config=ScraperConfig(params={"start_url": url, "max_pages": 5}),
            schedule_priority=random.choice(
                [
                    ScraperJobPriority.HIGH,
                    ScraperJobPriority.UTMOST,
                    ScraperJobPriority.NORMAL,
                ]
            ),
        )
        for id, url in enumerate(urls)
    ]


def get_scrapers_storage(urls: list[str], is_read_only: bool) -> ScrapersStorage:
    return InMemoryScrapersStorage(
        scrapers=get_scrapers(urls), is_read_only=is_read_only
    )


def get_server(urls: list[str], is_read_only: bool) -> SneakpeekServer:
    return SneakpeekServer.create(
        handlers=[DemoScraper()],
        scrapers_storage=get_scrapers_storage(urls, is_read_only),
        jobs_storage=InMemoryScraperJobsStorage(),
        lease_storage=InMemoryLeaseStorage(),
        plugins=[
            RequestsLoggingPlugin(),
            RobotsTxtPlugin(),
            RateLimiterPlugin(RateLimiterPluginConfig(max_rpm=60)),
            UserAgentInjecterPlugin(
                UserAgentInjecterPluginConfig(use_external_data=False)
            ),
        ],
    )


def main():
    args = parser.parse_args()
    server = get_server(args.urls, args.read_only)
    configure_logging()
    server.serve()


if __name__ == "__main__":
    main()
