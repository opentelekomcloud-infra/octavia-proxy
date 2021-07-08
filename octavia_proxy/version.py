import pbr.version

OCTAVIA_VENDOR = "Open Telekom Cloud"
OCTAVIA_PRODUCT = "Octavia-Proxy"

version_info = pbr.version.VersionInfo('octavia-proxy')


def vendor_string():
    return OCTAVIA_VENDOR


def product_string():
    return OCTAVIA_PRODUCT


def version_string_with_package():
    return version_info.version_string()
