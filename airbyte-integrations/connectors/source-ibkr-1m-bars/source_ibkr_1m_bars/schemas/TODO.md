#Test check
poetry run source-ibkr-1m-bars check --config secrets/config.json

#Test read
poetry run source-ibkr-1m-bars read --config secrets/config.json --catalog integration_tests/configured_catalog.json

#build docker image
docker build . -t airbyte/source-ibkr-1m-bars:dev

#Tag image
docker tag airbyte/source-ibkr-1m-bars:dev vps03.colinweber.com/airbyte/source-ibkr-1m-bars:dev

#push to my container registry
docker push vps03.colinweber.com/airbyte/source-ibkr-1m-bars:dev


#change stream state manually in connector GUI to 
 "streamState": {
      "date": "2000-01-01T18:49:00+00:00",
      "end": "2017-08-01T18:49:00+00:00"
}

#end is the ending date range, date is the beginning of the range.