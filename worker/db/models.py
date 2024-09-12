from sqlalchemy import DECIMAL, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TicketPrice(Base):
    __tablename__ = "ticket_prices"

    id = Column(Integer, primary_key=True, index=True)
    start_station = Column(String(50), nullable=False, index=True)
    end_station = Column(String(50), nullable=False)
    full_ticket_price = Column(Integer, nullable=False)
    senior_card_price = Column(Integer, nullable=False)
    taipei_child_discount = Column(Integer, nullable=True)

class StationTime(Base):
    __tablename__ = 'station_times'

    id = Column(Integer, primary_key=True, autoincrement=True)
    startStationId  = Column(String(10), nullable=False)
    startStation = Column(String(50), nullable=False, index=True)
    endStationId = Column(String(10), nullable=False)
    endStation = Column(String(50), nullable=False)
    arriveTime = Column(Integer, nullable=False)

class Station(Base):
    __tablename__ = 'stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)

    parking_lots = relationship("ParkingLot", back_populates="station")
    bus_routes = relationship("BusRoute", back_populates="station")

class ParkingLot(Base):
    __tablename__ = 'parking_lots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey('stations.id'))
    name = Column(String(255), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)

    station = relationship("Station", back_populates="parking_lots")

class MRTStation(Base):
    __tablename__ = 'mrt_stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(10), nullable=False,index=True)
    station_sid = Column(String(10), nullable=False)
    station_name = Column(String(100), nullable=False,index=True)
    stations_for_bus = Column(String(20),nullable=False)
    station_name_en = Column(String(100), nullable=False)
    longitude = Column(DECIMAL(9, 6), nullable=False)
    latitude = Column(DECIMAL(8, 6), nullable=False)


class YoubikeStation(Base):
    __tablename__ = 'youbike_stations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String(50), nullable=False, index=True)
    bike_name = Column(String(100), nullable=False)
    bike_uid = Column(String(20), nullable=False)
    bike_latitude = Column(DECIMAL(9, 6), nullable=False)
    bike_longitude = Column(DECIMAL(8, 6), nullable=False)
    bike_address = Column(String(200), nullable=True)

class BusRoute(Base):
    __tablename__ = 'bus_routes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey('stations.id'), nullable=False, index=True)
    stop_name = Column(String(255), nullable=False)
    route_name = Column(String(255), nullable=False, index=True)
    departure = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    station = relationship("Station", back_populates="bus_routes")


