from prometheus_client.core import GaugeMetricFamily

from netbox_metrics_ext import custom_metric

@custom_metric
def metric_devices():
    
    g = GaugeMetricFamily("dynamic_load_test", "Dynamic metric sample", value=10)
    
    yield g