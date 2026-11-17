import { Actor, log } from 'apify';
import { CheerioCrawler } from 'crawlee';

await Actor.init();

const {
    startUrls = [],
    maxRequestsPerCrawl = 50,
    maxDepth = 1,
    sameDomainOnly = true,
    includeLinks = false,
    proxyConfiguration: proxyInput,
} = (await Actor.getInput()) ?? {};

if (!startUrls.length) {
    throw new Error('Input "startUrls" must contain at least one URL.');
}

const proxyConfiguration = proxyInput
    ? await Actor.createProxyConfiguration(proxyInput)
    : undefined;

const crawler = new CheerioCrawler({
    proxyConfiguration,
    maxRequestsPerCrawl: maxRequestsPerCrawl > 0 ? maxRequestsPerCrawl : undefined,
    async requestHandler({ request, $, enqueueLinks }) {
        const depth = request.userData.depth ?? 0;
        log.info(`Scraping ${request.loadedUrl} (depth ${depth})`);

        const links = [
            ...new Set(
                $('a[href]')
                    .map((_, el) => {
                        try {
                            return new URL($(el).attr('href'), request.loadedUrl).href;
                        } catch {
                            return null;
                        }
                    })
                    .get()
                    .filter((href) => href && href.startsWith('http')),
            ),
        ];

        const item = {
            url: request.loadedUrl,
            title: $('title').first().text().trim() || null,
            description: $('meta[name="description"]').attr('content')?.trim() || null,
            h1: $('h1').map((_, el) => $(el).text().trim()).get().filter(Boolean),
            h2: $('h2').map((_, el) => $(el).text().trim()).get().filter(Boolean),
            linkCount: links.length,
            depth,
            scrapedAt: new Date().toISOString(),
        };
        if (includeLinks) item.links = links;

        await Actor.pushData(item);

        if (depth < maxDepth) {
            await enqueueLinks({
                strategy: sameDomainOnly ? 'same-hostname' : 'all',
                userData: { depth: depth + 1 },
            });
        }
    },
    failedRequestHandler({ request }, error) {
        log.error(`Request ${request.url} failed: ${error.message}`);
    },
});

await crawler.run(startUrls);

await Actor.exit();
