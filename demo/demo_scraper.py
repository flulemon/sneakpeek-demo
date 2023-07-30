import asyncio
import json
import logging
from urllib.parse import urljoin

from pydantic import BaseModel
from sneakpeek.logging import configure_logging
from sneakpeek.middleware.parser import ParserMiddleware
from sneakpeek.middleware.rate_limiter_middleware import (
    RateLimiterMiddleware,
    RateLimiterMiddlewareConfig,
)
from sneakpeek.middleware.requests_logging_middleware import RequestsLoggingMiddleware
from sneakpeek.scraper.context import ScraperContext
from sneakpeek.scraper.model import ScraperConfig, ScraperContextABC, ScraperHandler
from sneakpeek.scraper.runner import ScraperRunner


# Demo class that holds information that
# we want to extract from the page
class PageMetadata(BaseModel):
    url: str
    title: str
    description: str


# This defines model of handler parameters that are defined
# in the scraper config and then passed to the handler
class DemoScraperParams(BaseModel):
    start_url: str
    max_pages: int


# This is a class which actually implements logic
# Note that you need to inherit the implementation from
# the `sneakpeek.scraper_handler.ScraperHandler`
class DemoScraper(ScraperHandler):
    # You can have any dependencies you want and pass them
    # in the server configuration
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    # Each handler must define its name so it later
    # can be referenced in scrapers' configuration
    @property
    def name(self) -> str:
        return "demo_scraper"

    # Some example function that processes the response
    # and extracts valuable information
    def process_page(
        self,
        context: ScraperContext,
        url: str,
        page: str,
    ) -> PageMetadata:
        title = context.parser.regex(page, r"<title>(?P<title>[^<]+)")
        description = context.parser.regex(
            page, r'meta content="(?P<description>[^"]+)" property="og:description'
        )

        return PageMetadata(
            url=url,
            title=title[0].groups["title"] if title else "",
            description=description[0].groups["description"] if description else "",
        )

    # Extract all links in the page
    def extract_next_links(
        self,
        context: ScraperContextABC,
        start_url: str,
        page: str,
    ) -> list[str]:
        return [
            urljoin(start_url, link.groups["href"])
            for link in context.parser.regex(page, r'a[^<]+href="(?P<href>[^"]+)')
        ]

    # This function is called by the worker to execute the logic
    # The only argument that is passed is `sneakpeek.scraper_context.ScraperContextABC`
    # It implements basic async HTTP client and also provides parameters
    # that are defined in the scraper config
    async def run(self, context: ScraperContextABC) -> str:
        params = DemoScraperParams.parse_obj(context.params)

        # Download start URL
        response = await context.get(params.start_url)
        page = await response.text()

        # Extract page metadata
        results = [self.process_page(context, params.start_url, page)]

        # Find next links to download
        next_links = self.extract_next_links(
            context,
            params.start_url,
            page,
        )[: params.max_pages]

        # Download next links
        responses = await asyncio.gather(
            *[context.get(link) for link in next_links], return_exceptions=True
        )

        # Process next links and extract some metadata
        for link, response in zip(next_links, responses):
            if isinstance(response, Exception):
                continue
            page = await response.text()
            results.append(self.process_page(context, link, page))

        # Return meaningful job summary - must return a string
        return json.dumps(
            {"total": len(results), "results": [r.title for r in results]}
        )


async def main():
    configure_logging(logging.DEBUG)
    result = await ScraperRunner.debug_handler(
        DemoScraper(),
        config=ScraperConfig(
            params=DemoScraperParams(
                start_url="https://www.ycombinator.com/",
                max_pages=20,
            ).dict(),
        ),
        middlewares=[
            RequestsLoggingMiddleware(),
            RateLimiterMiddleware(RateLimiterMiddlewareConfig()),
            ParserMiddleware(),
        ],
    )
    logging.info(f"Finished scraper with result: {result}")


if __name__ == "__main__":
    main()
