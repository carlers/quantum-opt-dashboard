FROM python:3.12-slim
WORKDIR /app
COPY framework/python framework/python
COPY problems problems
COPY apps/worker apps/worker
RUN pip install --no-cache-dir ./framework/python \
 && pip install --no-cache-dir ./problems/water_quality \
 && pip install --no-cache-dir ./apps/worker
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "qopt.worker.entrypoint"]
