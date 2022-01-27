# Wekan Prometheus exporter

This Docker image is simply running a Python script that collect some information from Wekan API and expose them on an HTTP `/metrics` endpoint for Prometheus.

Here is a list of some environment variables you should set :

- `API_URL`: full URL of the Wekan instance (eg. `https://kanban.yourdomain.com`)
- `EXPORTER_API_USER`: admin user on Wekan API (defaults to `admin`)
- `EXPORTER_API_PASSWORD`: password for the user
- `EXPORTER_COLLECT_INTERVAL`: number of seconds between 2 refresh of the metrics (defaults to `60`)
- `INSTANCE_NAME`: instance name to add as a tag on metrics

# Source

- Originally from [this gist](https://gist.github.com/pichouk/2040c30127bec7a561d31d646c4571a7)
  at [this Prometheus metrics WeKan issue](https://github.com/wekan/wekan/issues/3535#issuecomment-1023528620).
