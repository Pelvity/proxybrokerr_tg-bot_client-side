from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class ProxyConnection:
    id: str
    userId: str
    createdTimestamp: int
    updatedTimestamp: int
    name: str
    description: str
    ip: str
    port: int
    login: str
    password: str
    type: str
    connectionId: str
    active: bool

@dataclass
class Proxy:
    id: int
    name: str
    authToken: str
    proxies: List[ProxyConnection]
    user: str  # Extracted username part
    expiration_date: datetime  # The expiration date of the proxy connection
    days_left: int  # The number of days left until expiration
    hours_left: int  # The number of hours left until expiration
    tariff_plan: str
    tariff_expiration_date: datetime
    tariff_days_left: int
    deviceModel: str
    active: bool
    service_name: str