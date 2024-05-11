# Import the dependencies.

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
from flask import Flask, jsonify
import datetime as dt
import numpy as np

#################################################
# Database Setup
#################################################

# reflect an existing database into a new model
# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Home page that lists the routes and what data they return
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the Honolulu, Hawaii weather API!<br/><br/>"
        f"Available Routes:<br/><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"<i>Provides precipitation data from all stations for the period of 8/23/16 to 8/23/17.</i><br/><br/>"
        f"/api/v1.0/stations<br/>"
        f"<i>Provides information about the stations.</i><br/><br/>"
        f"/api/v1.0/tobs<br/>"
        f"<i>Provides temperature data from the most active station for the period of 8/23/16 to 8/23/17.</i><br/><br/>"
        f"/api/v1.0/[start]<br/>"
        f"<i>Provides temperature data (max, min, mean) for the date range from the starting date entered through 8/23/17. Format start date as YYYY-MM-DD. Data available between 1/1/10 to 8/23/17.</i><br/><br/>"
        f"/api/v1.0/[start]/[end]<br/>"
        f"<i>Provides temperature data (max, min, mean) for the date range specified. Format start and end dates as YYYY-MM-DD. Data available between 1/1/10 to 8/23/17.</i>"
    )

# Route to JSONified precipitation data for the final year of data
@app.route("/api/v1.0/precipitation")
def precip():
# Create our session (link) from Python to the DB
    session = Session(engine)

# Find the most recent data point in the database. 
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date

# Calculate the date one year from the last date in data set.
    one_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)

# Perform a query to retrieve the data and precipitation scores
    precip_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year).order_by(Measurement.date).all()

# Set up a list and save the precipitation data for each date in dictionaries within the list
    all_precip_data = []
    for date, prcp in precip_data:
        precip_dict = {}
        precip_dict['date'] = date
        precip_dict['precip'] = prcp
        all_precip_data.append(precip_dict)

# Return the list of dictionaries as JSONified data
    return jsonify(all_precip_data)

#Close the session
    session.close()

#Route to provide JSONified data on each station
@app.route("/api/v1.0/stations")
def stations():
# Create our session (link) from Python to the DB
    session = Session(engine)

# Query the data about each station from the station database
    results = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

# Set up a list and save the station data in dictionaries within the list 
    all_stations = []
    for id, station, name, latitude, longitude, elevation in results:
        station_dict = {}
        station_dict['id'] = id
        station_dict['station'] = station
        station_dict['name'] = name
        station_dict['latitude'] = latitude
        station_dict['longitude'] = longitude
        station_dict['elevation'] = elevation
        all_stations.append(station_dict)

# Return the JSONified list of dictionaries    
    return jsonify(all_stations)

#Close the session
    session.close()

#Route to provide temperature data from the most active station for the final year of data
@app.route("/api/v1.0/tobs")
def temps():
# Create our session (link) from Python to the DB
    session = Session(engine)

# Calculate the start date (one year prior to last available date of data)
    one_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)

# Find the most active station by counting the number of rows of each session and selecting the first one in sorted list
    activity = session.query(Measurement.station, func.count(Measurement.station)).\
    group_by(Measurement.station).\
    order_by(func.count(Measurement.station).desc())
    most_active = activity.first()[0]

# Gather the temperature observation data from the most active station for the one-year period
    temp_data = session.query(Measurement.date, Measurement.tobs).\
    filter(Measurement.station == most_active).\
    filter(Measurement.date >= one_year).all()

#Create a list and save the temperature data in dictionaries within the list
    all_temps = []
    for date, tobs in temp_data:
        temp_dict = {}
        temp_dict['date'] = date
        temp_dict['temp'] = tobs
        all_temps.append(temp_dict)

#Return a JSONified version of the list of dictinoaries    
    return jsonify(all_temps)

# Close the session
    session.close()

# Route to provide max, min, and avg temperature data over a user-defined period starting with a start date and ending with the final date in the database
@app.route("/api/v1.0/<start>")
def temp_range_start(start):
# Create our session (link) from Python to the DB
    session = Session(engine)

# Calculate most recent date in database
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date

# Query temperature data (max, min, mean) for date range starting at user's inputted start date
    start_temp_data = session.query(func.max(Measurement.tobs), func.min(Measurement.tobs), func.avg(Measurement.tobs)).\
    filter(Measurement.date >= start).all()

# Create a list and save the temperature data in dictionaries within the list
    start_temps = []
    for max_temp, min_temp, avg_temp in start_temp_data:
        temp_dict = {}
        temp_dict['start date'] = start
        temp_dict['end date'] = recent_date
        temp_dict['max temp'] = max_temp
        temp_dict['min temp'] = min_temp
        temp_dict['avg temp'] = round(avg_temp,1)
        start_temps.append(temp_dict)

# Return a JSONified version of the list of dictionaries
    return jsonify(start_temps)

# Close the session
    session.close()

# Route to provide max, min, and avg temperature data over a user-defined period with inputted start/end dates
@app.route("/api/v1.0/<start>/<end>")
def temp_range_start_end(start, end):
# Create our session (link) from Python to the DB
    session = Session(engine)

# Query temperature data (max, min, mean) for user's inputted date range
    start_end_temp_data = session.query(func.max(Measurement.tobs), func.min(Measurement.tobs), func.avg(Measurement.tobs)).\
    filter(Measurement.date.between(start, end)).all()

# Create a list and save the temperature data in dictionaries within the list
    start_end_temps = []
    for max_temp, min_temp, avg_temp in start_end_temp_data:
        temp_dict = {}
        temp_dict['start date'] = start
        temp_dict['end date'] = end
        temp_dict['max temp'] = max_temp
        temp_dict['min temp'] = min_temp
        temp_dict['avg temp'] = round(avg_temp,1)
        start_end_temps.append(temp_dict)

# Return a JSONified version of the list of dictionaries
    return jsonify(start_end_temps)

# Close the session
    session.close()


if __name__ == '__main__':
    app.run(debug=True)