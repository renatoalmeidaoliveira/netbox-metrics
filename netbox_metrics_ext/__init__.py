"""Plugin declaration for netbox_metrics_ext."""
from netbox.plugins import PluginConfig

from .version import __version__

# Registry of functions that can generate additional application metrics
# All functions in the registry should take no argument and return an Iterator (or list) of prometheus Metric Object
# The Registry can be populated from the configuration file or using register_metric_func()
__REGISTRY__ = []


def register_metric_func(func):
    """Register an additional function to generate application metrics.

    Args:
        func: python function, taking no argument that return a list of Prometheus Metric Object
    """
    if not callable(func):
        raise TypeError(
            f"Trying to register a {type(func)} into the application metric registry, only function (callable) are supporter"
        )

    __REGISTRY__.append(func)

def custom_metric(func):

    __REGISTRY__.append(func)   
        
    return func

class MetricsExtConfig(PluginConfig):
    """Plugin configuration for the netbox_metrics_ext plugin."""

    name = "netbox_metrics_ext"
    verbose_name = "Metrics & Monitoring Extension Plugin"
    version = __version__
    author = "Renato Almeida de Oliveira Zaroubin"
    author_email = "renato.almeida.oliveira@gmail.com"
    description = "Plugin to improve the instrumentation of NetBox and expose additional metrics (Application Metrics, RQ Worker)."
    base_url = "metrics-ext"
    required_settings = []
    min_version = "4.0.0"
    max_version = "4.1.99"
    default_settings = {
        "app_metrics": {
            "models": {
                "dcim": {"Site": True, "Rack": True, "Device": True,},
                "ipam": {"IPAddress": True, "Prefix": True},
            },
            "reports": True,
            "queues": True,
        }
    }
    caching_config = {}


config = MetricsExtConfig  # pylint:disable=invalid-name
