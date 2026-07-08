# CAMS API Manager Deployment

This note records the cloud deployment mode introduced on 2026-06-22.

## Why

The cloud server has about 1.6 GB memory. Keeping both heavy Python APIs online
at the same time leaves too little free memory:

- new-question API: about 500-700 MB after runtime load
- student-QA API: about 500 MB after runtime load
- manager process: about 10-20 MB

So the cloud deployment now keeps only a lightweight manager online and starts a
heavy worker only when an analysis POST request arrives.

## Runtime Layout

- Manager script: `/opt/cams/runtime/cams_api_manager.py`
- Source copy: `cams工作台/scripts/cams_api_manager.py`
- Systemd service: `cams-api-manager.service`
- Manager port: `127.0.0.1:8780`
- New-question worker port: `127.0.0.1:8765`
- Student-QA worker port: `127.0.0.1:8766`
- Idle worker timeout: `600` seconds

## Nginx Routing

Cloud Nginx routes both public API prefixes to the manager:

```nginx
location /cams-api/new-question/ {
    proxy_pass http://127.0.0.1:8780/cams-api/new-question/;
}

location /cams-api/student-qa/ {
    proxy_pass http://127.0.0.1:8780/cams-api/student-qa/;
}
```

The frontend does not need to change.

## Behavior

- `GET /health`, `GET /drafts`, `GET /drafts/:id`, and `DELETE /drafts/:id`
  are handled directly by the manager when possible.
- `POST /analyze` starts the relevant heavy worker on demand.
- Before starting one heavy worker, the manager stops the other idle worker.
- If the other worker is currently processing a request, the manager refuses the
  switch instead of killing an in-progress task.
- Idle workers are stopped automatically after `CAMS_API_IDLE_SECONDS`.

## Useful Commands

```bash
systemctl status cams-api-manager.service --no-pager -l
journalctl -u cams-api-manager.service -f
ss -ltnp | grep -E '8765|8766|8780'
free -h
```

## Rollback

The cloud server keeps a rollback nginx config at:

```text
/etc/nginx/sites-available/ai-math.rollback-before-cams-manager-20260622
```

Rollback steps:

```bash
systemctl disable --now cams-api-manager.service
cp /etc/nginx/sites-available/ai-math.rollback-before-cams-manager-20260622 /etc/nginx/sites-available/ai-math
nginx -t && systemctl reload nginx
```

Then start the original two API workers manually or with the previous startup
commands.
