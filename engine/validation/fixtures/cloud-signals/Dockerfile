# Intentionally minimal service image for Cloud Readiness validation.
# TEST-ONLY — do not deploy.
FROM alpine:3.19
WORKDIR /app
COPY app/hello.sh /app/hello.sh
RUN chmod +x /app/hello.sh
CMD ["/app/hello.sh"]
