FROM python:3.12-slim
WORKDIR /opt/cleanframe
COPY hisense/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY LICENSE THIRD_PARTY_NOTICES.md ./
COPY hisense ./hisense
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 SIDEE_STATE_DIR=/data
EXPOSE 4795
CMD ["python", "hisense/server.py", "serve", "--bind", "0.0.0.0"]
