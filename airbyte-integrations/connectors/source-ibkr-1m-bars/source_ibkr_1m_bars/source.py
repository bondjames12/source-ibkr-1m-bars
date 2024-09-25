from abc import ABC
from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple
import logging
import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator
from ib_insync import *

logger = logging.getLogger("airbyte")
"""
TODO: Most comments in this class are instructive and should be deleted after the source is implemented.

This file provides a stubbed example of how to use the Airbyte CDK to develop both a source connector which supports full refresh or and an
incremental syncs from an HTTP API.

The various TODOs are both implementation hints and steps - fulfilling all the TODOs should be sufficient to implement one basic and one incremental
stream from a source. This pattern is the same one used by Airbyte internally to implement connectors.

The approach here is not authoritative, and devs are free to use their own judgement.

There are additional required TODOs in the files within the integration_tests folder and the spec.yaml file.
"""

class BarSteam(Stream, ABC):
    primary_key = ["symbol","date"]
    cursor_field = "date"  # Assuming your data has a 'date' field
    state_checkpoint_interval = 5000  # Checkpoint after each successful request


class Bars(BarSteam):
    def __init__(self, config: Mapping[str, Any]):
        super().__init__()
        self.config = config
        

    def get_updated_state(self, current_stream_state: MutableMapping[str, Any], latest_record: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Override to determine the latest state after reading the latest record. This typically compared the cursor_field from the latest record and
        the current state and picks the 'most' recent cursor. This is how a stream's state is determined. Required for incremental.
        """
        """
        Update the state with the latest date from the fetched records.
        """
        current_state = current_stream_state.get(self.cursor_field, None)
        latest_record_date = latest_record.get(self.cursor_field, None)
        #logger.info(f"current_state: {current_state}")
        if current_state and type(current_state) is str:
            # Parse the last synced date from the state
            try:
                current_state = datetime.strptime(current_state, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=timezone.utc)
            except ValueError:
                current_state = datetime.strptime(current_state, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=timezone.utc)
        #logger.info(f"latest_record_date: {latest_record_date}")
        if latest_record_date and type(latest_record_date) is str:
            # Parse the last synced date from the state
            try:
                latest_record_date = datetime.strptime(latest_record_date, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=timezone.utc)
            except ValueError:
                latest_record_date = datetime.strptime(latest_record_date, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=timezone.utc)

        if latest_record_date and (not current_state or latest_record_date > current_state):
            current_stream_state[self.cursor_field] = latest_record_date
        return current_stream_state

    def read_records(self, stream_state: Mapping[str, Any] = None, **kwargs) -> Iterable[Mapping[str, Any]]:
        stream_state = stream_state or {}
        logger.info(f"stream_state: {stream_state}")
        ib = IB()
        ib.connect(self.config["host"], self.config["port"], self.config["clientid"])
        symbol = self.config["symbol"]
        start_date = self._get_start_date(stream_state)
        logger.info(f"Start Date: {start_date}")
        end_date = stream_state.get("end", datetime.now(timezone.utc))
        if end_date and type(end_date) is str:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=timezone.utc)
            except ValueError:
                end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=timezone.utc)
            stream_state.pop('end', None)
        readHighestDate = end_date
        logger.info(f"End Date_: {end_date}")
        contract = Stock(symbol, self.config["exchange"], self.config["currency"])
        while start_date < end_date:
            bars = ib.reqHistoricalData(
                contract,
                endDateTime=end_date,
                durationStr='10 D',
                barSizeSetting='1 min',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=2  # Date will use UTC timezone
            )
            logger.info(f"Got: {bars.__len__()} bars from IBKR API")
            if not bars:
                break
            end_date = bars[0].date
            logger.info(f"Got date until: " + str(end_date))

            for bar in bars:
                # Transform BarData object to dictionary
                bar_as_dict = {
                    'symbol': symbol,
                    'date': bar.date,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'average': bar.average,
                    'barCount': bar.barCount
                }
                yield bar_as_dict
                # Update the state with the latest record's date
                #just set end_date
                stream_state[self.cursor_field] = end_date
        stream_state[self.cursor_field] = readHighestDate
        ib.disconnect()

        

    def _get_start_date(self, stream_state: Mapping[str, Any]) -> datetime:
        """
        Determine the start date for fetching data.
        """
        # Get the user-provided start date from the config
        user_start_date = self.config.get('startdate')
        logger.info(f"Config Start Date: {user_start_date}")
        if user_start_date:
                start_date = datetime.strptime(user_start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        # If there's existing state, use the last synced date
        last_synced_str = stream_state.get(self.cursor_field)
        logger.info(f"Stream Start Start Date: {last_synced_str}")
        if last_synced_str:
            # Parse the last synced date from the state
            try:
                last_synced_date = datetime.strptime(last_synced_str, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=timezone.utc)
            except ValueError:
                last_synced_date = datetime.strptime(last_synced_str, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=timezone.utc)
            # Use the max of user_start_date and last_synced_date
            return max(start_date, last_synced_date)
        else:
            return start_date

    
 #   def stream_slices(self, stream_state: Mapping[str, Any] = None, **kwargs) -> Iterable[Optional[Mapping[str, any]]]:
        """
        TODO: Optionally override this method to define this stream's slices. If slicing is not needed, delete this method.

        Slices control when state is saved. Specifically, state is saved after a slice has been fully read.
        This is useful if the API offers reads by groups or filters, and can be paired with the state object to make reads efficient. See the "concepts"
        section of the docs for more information.

        The function is called before reading any records in a stream. It returns an Iterable of dicts, each containing the
        necessary data to craft a request for a slice. The stream state is usually referenced to determine what slices need to be created.
        This means that data in a slice is usually closely related to a stream's cursor_field and stream_state.

        An HTTP request is made for each returned slice. The same slice can be accessed in the path, request_params and request_header functions to help
        craft that specific request.

        For example, if https://example-api.com/v1/employees offers a date query params that returns data for that particular day, one way to implement
        this would be to consult the stream state object for the last synced date, then return a slice containing each date from the last synced date
        till now. The request_params function would then grab the date from the stream_slice and make it part of the request by injecting it into
        the date query param.
        """
 #       raise NotImplementedError("Implement stream slices or delete this method!")


# Source
class SourceIbkr_1mBars(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        """
        Implement a connection check to validate that the user-provided config can be used to connect to the underlying API
        See https://github.com/airbytehq/airbyte/blob/master/airbyte-integrations/connectors/source-stripe/source_stripe/source.py#L232
        for an example.
        :param config:  the user-input config object conforming to the connector's spec.yaml
        :param logger:  logger object
        :return Tuple[bool, any]: (True, None) if the input config can be used to connect to the API successfully, (False, error) otherwise.
        """
        logger.info("Checking IB API connection...")
        host = config["host"]
        port = config["port"]
        clientid = config["clientid"]
        timeout = config["timeout"]
        readonly = config["readonly"]
        symbol = config["symbol"]
        exchange = config["exchange"]
        currency = config["currency"]
        # Connect to IB
        ib = IB()
        try:
            ib.connect(host,port, clientid, timeout, readonly)
        except Exception as e:
            return False, f"Could not connect to IB: {e}"
        contract = Stock(symbol, exchange, currency)
        bars = ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='1 hour',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=2  # Date will use UTC timezone
        )
        if not bars:
            return False, f"Connection succeeded but no historical data returned for f{symbol} in the last 1 day."
        ib.disconnect()
        return True, None

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        """
        Replace the streams below with your own streams.
        :param config: A Mapping of the user input configuration as defined in the connector spec.
        """
        # remove the authenticator if not required.
        #auth = TokenAuthenticator(token="api_key")  # Oauth2Authenticator is also available if you need oauth support
        return [Bars(config=config)]
