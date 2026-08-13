# RIST AWS Asset Pipeline

Target flow: source assets -> S3 private asset bucket -> CloudFront CDN -> RIST Blazor client.

The client must reference a configurable asset base URL and never depend on Google Drive browser hotlinks.
