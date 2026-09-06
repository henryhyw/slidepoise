# Security

Please report a suspected vulnerability privately through GitHub Security Advisories for this repository. Include the affected version, a minimal reproduction, and the expected impact.

SlidePoise processes local presentation assets. Treat files from unknown sources as untrusted. The supported visual input path uses PNG, JPEG, SVG, and WebP assets. Keep the framework and its Python and Node dependencies current.

PptxGenJS currently brings in `image-size`, whose ICNS, JXL, and HEIF parsers have unresolved denial-of-service advisories in the published npm releases. SlidePoise does not accept those formats through its supported asset path. We will update the transitive dependency when an upstream patched release is available.
