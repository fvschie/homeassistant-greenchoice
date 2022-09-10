from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs

import bs4
import requests
from requests import Session

from .const import (
    API_URL,
    LOGGER,
    MEASUREMENT_TYPES,
    SERVICE_METERSTAND_STROOM,
    SERVICE_METERSTAND_GAS,
    SERVICE_TARIEVEN,
    MeasurementNames
)


class GreenchoiceOvereenkomst:

    def __init__(self, postcode: str, huisnummer: int, city: str, overeenkomst_id: int):
        self.postcode = postcode
        self.huisnummer = huisnummer
        self.city = city
        self.overeenkomst_id = overeenkomst_id

    def get_location(self) -> str:
        return f"{self.postcode} nr {self.huisnummer}, {self.city}"

    def __str__(self) -> str:
        location = f"{self.postcode} nr {self.huisnummer}, {self.city}".ljust(30, " ")
        return f"{self.overeenkomst_id} ({location})"

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.postcode}',{self.huisnummer},'{self.city}',{self.overeenkomst_id})"


class GreenchoiceApiData:
    class Measurement(Dict[MeasurementNames, float | datetime]):
        pass

    def __init__(self, meterstand_stroom: Measurement, meterstand_gas: Measurement, tarieven: Measurement) -> None:
        self.meterstand_stroom = meterstand_stroom
        self.meterstand_gas = meterstand_gas
        self.tarieven = tarieven

    def __getitem__(self, item):
        if item not in [SERVICE_METERSTAND_STROOM, SERVICE_METERSTAND_GAS, SERVICE_TARIEVEN]:
            raise GreenchoiceError(f"Unable to retrieve item with key {item}")
        return self.__dict__[item]


class GreenchoiceError(Exception):
    pass


class GreenchoiceApi:

    def __init__(self, username: str, password: str) -> None:
        self.username: str = username
        self.password: str = password
        self.session: Optional[Session] = None

    def login(self):
        self.session = self.__get_session()

    @staticmethod
    def __get_verification_token(html_txt: str):
        soup = bs4.BeautifulSoup(html_txt, "html.parser")
        token_elem = soup.find("input", {"name": "__RequestVerificationToken"})

        return token_elem.attrs.get("value")

    @staticmethod
    def __get_oidc_params(html_txt: str):
        soup = bs4.BeautifulSoup(html_txt, "html.parser")

        code_elem = soup.find("input", {"name": "code"})
        scope_elem = soup.find("input", {"name": "scope"})
        state_elem = soup.find("input", {"name": "state"})
        session_state_elem = soup.find("input", {"name": "session_state"})

        if not (code_elem and scope_elem and state_elem and session_state_elem):
            error = "Login failed, check your credentials?"
            LOGGER.error(error)
            raise (GreenchoiceError(error))

        return {
            "code": code_elem.attrs.get("value"),
            "scope": scope_elem.attrs.get("value").replace(" ", "+"),
            "state": state_elem.attrs.get("value"),
            "session_state": session_state_elem.attrs.get("value")
        }

    def __get_session(self) -> Session:
        if not self.username or not self.password:
            error = "Username or password not set"
            LOGGER.error(error)
            raise (GreenchoiceError(error))
        sess: Session = requests.Session()

        # first, get the login cookies and form data
        login_page = sess.get(API_URL)

        login_url = login_page.url
        return_url = parse_qs(urlparse(login_url).query).get("ReturnUrl", "")
        token = GreenchoiceApi.__get_verification_token(login_page.text)

        # perform actual sign in
        login_data = {
            "ReturnUrl": return_url,
            "Username": self.username,
            "Password": self.password,
            "__RequestVerificationToken": token,
            "RememberLogin": True
        }
        auth_page = sess.post(login_page.url, data=login_data)

        # exchange oidc params for a login cookie (automatically saved in session)
        oidc_params = GreenchoiceApi.__get_oidc_params(auth_page.text)
        sess.post("https://mijn.greenchoice.nl/signin-oidc", data=oidc_params)
        return sess

    def get_overeenkomsten(self) -> List[GreenchoiceOvereenkomst]:
        # retrieve overeenkomsten
        init_data = self.session.get("https://mijn.greenchoice.nl/microbus/init").json()
        customer_number = init_data["profile"]["voorkeursOvereenkomst"]["klantnummer"]
        customer = next((customer for customer in init_data["klantgegevens"]
                         if customer["klantnummer"] == customer_number), None)
        if customer is None:
            error = f"Could not find customer details with ID {customer_number}"
            LOGGER.error(error)
            raise (GreenchoiceError(error))

        addresses = customer["adressen"]
        return list(map(lambda address: GreenchoiceOvereenkomst(
            address.get("postcode", ""),
            address.get("huisnummer", None),
            address.get("plaats").capitalize(),
            address["overeenkomstId"]), addresses))

    def __request(self, method, endpoint, data=None, _retry_count=1):
        LOGGER.debug(f'Request: {method} {endpoint}')
        try:
            target_url = API_URL + endpoint
            r = self.session.request(method, target_url, json=data)

            if r.status_code == 403 or len(r.history) > 1:  # sometimes we get redirected on token expiry
                LOGGER.debug('Access cookie expired, triggering refresh')
                try:
                    return self.__request(method, endpoint, data, _retry_count)
                except GreenchoiceError:
                    LOGGER.error('Login failed! Please check your credentials and try again.')
                    return None

            r.raise_for_status()
        except requests.HTTPError as e:
            LOGGER.error(f'HTTP Error: {e}')
            LOGGER.error([c.name for c in self.session.cookies])
            if _retry_count == 0:
                return None

            LOGGER.debug('Retrying request')
            return self.__request(method, endpoint, data, _retry_count - 1)

        return r

    def __microbus_request(self, name, message=None):
        if not message:
            message = {}

        payload = {
            'name': name,
            'message': message
        }
        response = self.__request('POST', '/microbus/request', payload)
        if not response:
            raise ConnectionError

        return response.json()

    @staticmethod
    def __get_most_recent_entries(values):
        current_month = sorted(filter(lambda v: 'opnames' in v and len(v['opnames']) > 0, values), key=lambda m: (m['jaar'], m['maand']), reverse=True)[0]
        if not current_month or len(current_month['opnames']) == 0:
            return None

        return sorted(
            current_month['opnames'],
            key=lambda d: datetime.strptime(d['opnameDatum'], '%Y-%m-%dT%H:%M:%S'),
            reverse=True
        )[0]

    def get_update(self, overeenkomst_id: int) -> Optional[GreenchoiceApiData]:
        LOGGER.debug('Retrieving meter values')
        try:
            monthly_values = self.__microbus_request('OpnamesOphalen')
        except requests.exceptions.JSONDecodeError | ConnectionError:
            LOGGER.error('Could not update meter values: request failed or returned no valid JSON', exc_info=True)
            return

        # parse energy data
        meterstand_stroom = GreenchoiceApi.__parse_meterstand_stroom(monthly_values)

        # process gas
        meterstand_gas = GreenchoiceApi.__parse_meterstand_gas(monthly_values)

        try:
            tariff_values = self.__microbus_request('GetTariefOvereenkomst', message={"overeenkomstId": overeenkomst_id})
        except requests.exceptions.JSONDecodeError:
            LOGGER.error('Could not update tariff values: request failed or returned no valid JSON')
            return

        # process tarieven
        tarieven = GreenchoiceApi.__parse_tarieven(tariff_values)
        return GreenchoiceApiData(meterstand_stroom, meterstand_gas, tarieven)

    @staticmethod
    def __parse_meterstand_stroom(monthly_values: dict) -> Optional[GreenchoiceApiData.Measurement]:
        if not monthly_values['model']['heeftStroom']:
            LOGGER.info("Not parsing electricity meter, contract doesn't have electricity")
            return None

        electricity_values = monthly_values['model']['productenOpnamesModel'][0]['opnamesJaarMaandModel']
        current_day = GreenchoiceApi.__get_most_recent_entries(electricity_values)
        if current_day is None:
            LOGGER.error('Could not update meter values: No current values for electricity found')
            return None

        meterstand_stroom = GreenchoiceApiData.Measurement()
        for measurement in current_day['standen']:
            measurement_type = MEASUREMENT_TYPES[measurement['telwerk']]
            match measurement_type:
                case 'consumption_high':
                    meterstand_stroom[MeasurementNames.ENERGY_HIGH_IN] = measurement['waarde']
                case 'consumption_low':
                    meterstand_stroom[MeasurementNames.ENERGY_LOW_IN] = measurement['waarde']
                case 'return_high':
                    meterstand_stroom[MeasurementNames.ENERGY_HIGH_OUT] = measurement['waarde']
                case 'return_low':
                    meterstand_stroom[MeasurementNames.ENERGY_LOW_OUT] = measurement['waarde']

        meterstand_stroom[MeasurementNames.ENERGY_TOTAL_IN] = meterstand_stroom[MeasurementNames.ENERGY_HIGH_IN] + meterstand_stroom[MeasurementNames.ENERGY_LOW_IN]
        meterstand_stroom[MeasurementNames.ENERGY_TOTAL_OUT] = meterstand_stroom[MeasurementNames.ENERGY_HIGH_OUT] + meterstand_stroom[MeasurementNames.ENERGY_LOW_OUT]

        meterstand_stroom[MeasurementNames.ENERGY_MEASUREMENT_DATE] = datetime.strptime(current_day['opnameDatum'], '%Y-%m-%dT%H:%M:%S')
        return meterstand_stroom

    @staticmethod
    def __parse_meterstand_gas(monthly_values: dict) -> Optional[GreenchoiceApiData.Measurement]:
        if not monthly_values['model']['heeftGas']:
            LOGGER.info("Not parsing gas meter, contract doesn't have gas")
            return None

        gas_values = monthly_values['model']['productenOpnamesModel'][1]['opnamesJaarMaandModel']
        current_day = GreenchoiceApi.__get_most_recent_entries(gas_values)
        if current_day is None:
            LOGGER.error('Could not update meter values: No current values for gas found')
            return None

        meterstand_gas = GreenchoiceApiData.Measurement()
        measurement = current_day['standen'][0]
        if measurement['telwerk'] == 5:
            meterstand_gas[MeasurementNames.GAS_IN] = measurement['waarde']

        meterstand_gas[MeasurementNames.GAS_MEASUREMENT_DATE] = datetime.strptime(current_day['opnameDatum'], '%Y-%m-%dT%H:%M:%S')
        return meterstand_gas

    @staticmethod
    def __parse_tarieven(tariff_values: dict) -> GreenchoiceApiData.Measurement:
        tarieven = GreenchoiceApiData.Measurement()
        tarieven[MeasurementNames.PRICE_ENERGY_LOW_IN] = tariff_values['stroom']['leveringLaagAllin']
        tarieven[MeasurementNames.PRICE_ENERGY_LOW_OUT] = tariff_values['stroom']['terugleveringLaagAllin']
        tarieven[MeasurementNames.PRICE_ENERGY_HIGH_IN] = tariff_values['stroom']['leveringHoogAllin']
        tarieven[MeasurementNames.PRICE_ENERGY_HIGH_OUT] = tariff_values['stroom']['terugleveringHoogAllin']
        tarieven[MeasurementNames.PRICE_ENERGY_SELL_PRICE] = tariff_values['stroom']['terugleverVergoeding']
        tarieven[MeasurementNames.PRICE_GAS_IN] = tariff_values['gas']['leveringAllin']
        tarieven[MeasurementNames.COST_ENERGY_YEARLY] = tariff_values['stroom']['totaleJaarlijkseKostenIncBtw']
        tarieven[MeasurementNames.COST_GAS_YEARLY] = tariff_values['gas']['totaleJaarlijkseKostenIncBtw']
        tarieven[MeasurementNames.COST_TOTAL_YEARLY] = tarieven[MeasurementNames.COST_ENERGY_YEARLY] + tarieven[MeasurementNames.COST_GAS_YEARLY]
        return tarieven
