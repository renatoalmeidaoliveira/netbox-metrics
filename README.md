# netbox-metrics

This plugin is a fork of (ntc-netbox-plugin-metrics-ext)[https://github.com/networktocode/ntc-netbox-plugin-metrics-ext] with support for newer NetBox versions, and some improvements.

The plugin is composed of multiple features that can be used independantly:
- Application Metrics Endpoint: prometheus endpoint at `/api/plugins/metrics-ext/app-metrics`
- RQ Worker Metrics Command: Add prometheus endpoint on each RQ worker

# Application Metrics Endpoint

NetBox already exposes some information via a Prometheus endpoint but the information currently available are mostly at the system level and not at the application level.
- **SYSTEM Metrics** are very useful to instrument code, track ephemeral information and get a better visibility into what is happening. (Example of metrics: nbr of requests, requests per second, nbr of exceptions, response time, etc ...) The idea is that when multiple instances of NetBox are running behind a load balancer each one will produce a different set of metrics and the monitoring system needs to collect these metrics from all running instances and aggregate them in a dashboard. NetBox exposes some system metrics at `localhost/metrics` [NetBox DOC](https://netbox.readthedocs.io/en/stable/additional-features/prometheus-metrics/).
- **APPLICATION Metrics** are at a higher level and represent information that is the same across all instances of an application running behind a load balancer. If I have 3 instances of NetBox running, there is no point to ask each of them how many Device objects I have in the database, since they will always return the same information. In this case, the goal is to expose only 1 endpoint that can be served by any running instance.

System metrics and application level metrics are complementary with each other

Currently the plugin exposes these simple metrics by default:
- RQ Queues stats
- Reports stats
- Models count (configurable via configuration.py)

## Add your own metrics

This plugin supports some options to generate and publish your own application metrics behind the same endpoint.

### Option 1 - Register function(s) via configuration.py.

It's possible to create your own function to generate some metrics and register it to the plugin in the configuration.py.
Here is an example where the custom function are centralized in a `metrics.py` file, located next to the main `configuration.py`.

```python
# metrics.py
from prometheus_client.core import GaugeMetricFamily

def metric_prefix_utilization():
    """Report prefix utilization as a metric per container."""
    from ipam.models import Prefix  # pylint: disable=import-outside-toplevel

    containers = Prefix.objects.filter(status="container").all()
    g = GaugeMetricFamily(
        "netbox_prefix_utilization", "percentage of utilization per container prefix", labels=["prefix", "role", "site"]
    )

    for container in containers:

        site = "none"
        role = "none"
        if container.role:
            role = container.role.slug

        if container.site:
            site = container.site.slug

        g.add_metric(
            [str(container.prefix), site, role], container.get_utilization(),
        )

    yield g
```
The new function can be imported in the `configuration.py` file and registered with the plugin.
```python
# configuration.py
from netbox.metrics import metric_prefix_utilization
PLUGINS_CONFIG = {
    "netbox_metrics_ext": {
      "app_metrics": {
        "extras": [
          metric_prefix_utilization
        ]
      }
    }
},
```

### Option 2 - Registry for third party plugins

Any plugin can include its own metrics to improve the visibility and/or the troubleshooting of the plugin itself.
Third party plugins can register their own function(s) using the `ready()` function as part of their PluginConfig class.

```python
# my_plugin/__init__.py
from netbox_metrics_ext import register_metric_func
from netbox.metrics import metric_circuit_bandwidth

class MyPluginConfig(PluginConfig):
    name = "netbox_myplugin"
    verbose_name = "Demo Plugin "
    # [ ... ]
    def ready(self):
        super().ready()
        register_metric_func(metric_circuit_bandwidth)
```

### Option 3 -  Metrics directory

Its possible to dynamically load metrics to the plugin, for that you need to configure add `metrics_folder` inside the plugin configuration with the path of your metrics folder.
For configure your custom metrics the NetBox user needs read/write permissions in the `metrics_folder` and your metric functions needs to use the `@custom_metric` decorator

#### Configuration sample

```python
# configuration.py
from netbox.metrics import metric_prefix_utilization
PLUGINS_CONFIG = {
    "netbox_metrics_ext": {
      "app_metrics": {
        "metrics_folder": "/opt/netbox/netbox/custom_metrics",
      }
    }
},
```

#### Custom metric sample
```python
from prometheus_client.core import GaugeMetricFamily

from netbox_metrics_ext import custom_metric

@custom_metric
def metric_devices():
    
    g = GaugeMetricFamily("dynamic_load_test", "Dynamic metric sample", value=10)
    
    yield g
```

## Parameters

The behavior of the app_metrics feature can be controlled with the following list of settings (under `netbox_metrics_ext > app_metrics`):
- `reports` boolean (default True), publish stats about the reports (success, warning, info, failure)
- `queues` boolean (default True), publish stats about RQ Worker (nbr of worker, nbr and type of job in the different queues)
- `models` nested dict, publish the count for a given object (Nbr Device, Nbr IP etc.. ). The first level must be the name of the module in lowercase (dcim, ipam etc..), the second level must be the name of the object (usually starting with a uppercase)
    ```python
    {
      "dcim": {"Site": True, "Rack": True, "Device": True,},
      "ipam": {"IPAddress": True, "Prefix": True}
    }
    ```
## Usage

Configure your Prometheus server to collect the application metrics at `/api/plugins/metrics-ext/app-metrics/`

```yaml
# Sample prometheus configuration
scrape_configs:
  - job_name: 'netbox_app'
    scrape_interval: 60s
    metrics_path: /api/plugins/metrics-ext/app-metrics
    static_configs:
      - targets: ['netbox']
```

# RQ Worker Metrics Endpoint

This plugin add a new django management command `rqworker_metrics` that is behaving identically to the default `rqworker` command except that this command also exposes a prometheus endpoint (default port 8001).

With this endpoint it become possible to instrument the tasks running asyncronously in the worker.

## Usage

The new command needs to be executed on the worker as a replacement for the default `rqworker`
```
python manage.py rqworker_metrics
```

The port used to expose the prometheus endpoint can be configured for each worker in CLI.
```
python manage.py rqworker_metrics --prom-port 8002
```

Since the rq-worker is based on a fork model, for this feature to work it''s required to use prometheus in multi processes mode.
To enable this mode the environment variable `prometheus_multiproc_dir` must be define and point at a valid directory.

# Installation

### Compatibility Matrix

| Plugin Version | NetBox Version|
|----------------|---------------|
|1.0.0           | 3.7.x         |
|2.0.0           | 4.0.x         |
|2.0.0           | 4.1.x         |

### Instaling the plugin 

The plugin is available as a Python package in pypi and can be installed with pip
```shell
pip install netbox-metrics
```


To ensure Application Metrics Plugin is automatically re-installed during future upgrades, create a file named `local_requirements.txt` (if not already existing) in the NetBox root directory (alongside `requirements.txt`) and list the `netbox-metrics` package:

```no-highlight
# echo netbox-metrics >> local_requirements.txt
```

Once installed, the plugin needs to be enabled in your `configuration.py`
```python
# In your configuration.py
PLUGINS = ["netbox_metrics_ext"]

# PLUGINS_CONFIG = {
#   "netbox_metrics_ext": {
#     "app_metrics": {
#       "models": {
#         "dcim": {"Site": True, "Rack": True, "Device": True,},
#          "ipam": {"IPAddress": True, "Prefix": True},
#        },
#        "reports": True,
#        "queues": True,
#       }
#     }
#   }
# }
```

## Included Grafana Dashboard

Included within this plugin is a Grafana dashboard which will work with the example configuration above. To install this dashboard import the JSON from [Grafana Dashboard](netbox_grafana_dashboard.json) into Grafana.

![Netbox Grafana Dashboard](netbox_grafana_dashboard.png)


## Default Metrics for the application metrics endpoint

By Default the plugin will generate the following metrics
```
# HELP netbox_queue_stats Per RQ queue and job status statistics
# TYPE netbox_queue_stats gauge
netbox_queue_stats{name="check_releases",status="finished"} 0.0
netbox_queue_stats{name="check_releases",status="started"} 0.0
netbox_queue_stats{name="check_releases",status="deferred"} 0.0
netbox_queue_stats{name="check_releases",status="failed"} 0.0
netbox_queue_stats{name="check_releases",status="scheduled"} 0.0
netbox_queue_stats{name="default",status="finished"} 0.0
netbox_queue_stats{name="default",status="started"} 0.0
netbox_queue_stats{name="default",status="deferred"} 0.0
netbox_queue_stats{name="default",status="failed"} 0.0
netbox_queue_stats{name="default",status="scheduled"} 0.0
# HELP netbox_report_stats Per report statistics
# TYPE netbox_report_stats gauge
netbox_report_stats{name="test_hostname",status="success"} 13.0
netbox_report_stats{name="test_hostname",status="warning"} 0.0
netbox_report_stats{name="test_hostname",status="failure"} 0.0
netbox_report_stats{name="test_hostname",status="info"} 0.0
# HELP netbox_model_count Per NetBox Model count
# TYPE netbox_model_count gauge
netbox_model_count{app="dcim",name="Site"} 24.0
netbox_model_count{app="dcim",name="Rack"} 24.0
netbox_model_count{app="dcim",name="Device"} 46.0
netbox_model_count{app="ipam",name="IPAddress"} 58.0
netbox_model_count{app="ipam",name="Prefix"} 18.0
# HELP netbox_app_metrics_processing_ms Time in ms to generate the app metrics endpoint
# TYPE netbox_app_metrics_processing_ms gauge
netbox_app_metrics_processing_ms 19.90485
```