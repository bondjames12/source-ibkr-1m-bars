
FROM airbyte/python-connector-base:1.1.0

COPY . ./airbyte/integration_code
RUN pip install ./airbyte/integration_code

# The entrypoint and default env vars are already set in the base image
ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]

#how to deploy to docker registry

#tag with correct name
#docker tag airbyte/source-ibkr-1m-bars:dev vps03.colinweber.com/airbyte/source-ibkr-1m-bars:dev

#push to registry
#docker login https://vps03.colinweber.com
#docker tag airbyte/source-ibkr-1m-bars:dev vps03.colinweber.com/airbyte/source-ibkr-1m-bars:dev