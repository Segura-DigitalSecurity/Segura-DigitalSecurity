# Segura Web Scraper (Apify Actor)

An [Apify](https://apify.com) Actor built with the Apify SDK and [Crawlee](https://crawlee.dev)'s `CheerioCrawler`.
It crawls from a list of start URLs and stores, for each page:

- `url`, `title`, meta `description`
- all `h1` and `h2` headings
- `linkCount` (and the full `links` list if `includeLinks` is on)
- crawl `depth` and `scrapedAt` timestamp

## Input

| Field | Default | Description |
| --- | --- | --- |
| `startUrls` | — (required) | Pages to start crawling from |
| `maxRequestsPerCrawl` | `50` | Page limit (`0` = unlimited) |
| `maxDepth` | `1` | Link depth to follow (`0` = start URLs only) |
| `sameDomainOnly` | `true` | Only follow links on the same hostname |
| `includeLinks` | `false` | Save every link found on each page |
| `proxyConfiguration` | none | Apify Proxy / custom proxy settings |

## Run locally

```bash
cd apify-scraper
npm install
mkdir -p storage/key_value_stores/default
echo '{"startUrls":[{"url":"https://crawlee.dev"}],"maxDepth":0}' > storage/key_value_stores/default/INPUT.json
npm start
```

Results are written to `storage/datasets/default/`.

## Deploy to Apify

```bash
npm install -g apify-cli
apify login
cd apify-scraper
apify push
```
