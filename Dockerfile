FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

ENV PYTHONUNBUFFERED=1

RUN microdnf upgrade --refresh -y --setopt=tsflags=nodocs && \
    microdnf update -y && \
    microdnf install python3-pip gcc python3-devel sqlite -y && \
    microdnf clean all && \
    pip install pip --upgrade && \
    pip install setuptools && \
    rm -rf /var/cache

RUN --mount=type=bind,source=requirements.txt,target=/requirements.txt \
    pip3 install --root-user-action ignore --no-cache-dir -r requirements.txt

COPY ./app /app

WORKDIR /app
EXPOSE 8000
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "caas:api"]
CMD ["2>&1"]
