#!/usr/bin/env python
import sys
from obspy import UTCDateTime, Stream, read_events
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException
from libcomcat.search import search, get_event_by_id
import argparse

parser = argparse.ArgumentParser(description='Get Earthquake Information')

parser.add_argument("-p", action="store_true", dest="plot",
                    default=False, required=False, help='Plot events')

parser.add_argument("-s", "--stime", action="store", dest="stime",
                    default=False, type=str, required = True,
                    help="Start time. Use formats compatible with UTCDateTime")

parser.add_argument("-e", "--etime", action="store", dest="etime",
                    default=False, type=str, required=False,
                    help="End time. Use formats compatible with UTCDateTime")

# Alternative option to -e end time
parser.add_argument("-n", "--number", action="store", dest="number",
                    default=False, type=float, help="# of days since start time")

parser.add_argument("-mM", action="store", dest="min_mag", required=False,
                    default=2.5, type=float, help="Minimum magnitude")

parser.add_argument("-MM", action="store", dest="max_mag", required=False,
                    default=9.9, type=float, help="Maximum magnitude")

parser.add_argument("-md", action="store", dest="min_dep", required=False,
                    default=0, type=float, help="Minimum depth (km)")

parser.add_argument("-Md", action="store", dest="max_dep", required=False,
                    default=1000, type=float, help="Maximum depth (km)")

parser.add_argument("-l", "--lat", action="store", dest="lat", default=0.0,
                    required=False, type=float, help="Latitude for search radius")

parser.add_argument("-L", "--lon", action="store", dest="lon", default=0.0,
                    required=False, type=float, help="Longitude for search radius")

parser.add_argument("-r", "--radius", action="store", dest="radius",
                    default=180, required=False, type=float, help="Search radius")

args = parser.parse_args()

# Set time constraints.
stime = UTCDateTime(args.stime)

if args.etime and args.number:
    print("Both end time (-e) and number of days window (-n) were selected.\
Defaulting to (-e) end time.")
    etime = UTCDateTime(args.etime)
elif args.etime:
    etime = UTCDateTime(args.etime)
elif args.number:
    etime = stime + 86400 * args.number
else:
    etime = UTCDateTime()
    print("No end time or # of days provided. Using current time as end time")

# Get events from catalog that satisfy constraints.
client = Client('USGS')
try:
    cat = client.get_events(starttime=stime, endtime=etime,
            minmagnitude=args.min_mag, maxmagnitude=args.max_mag,
            latitude=args.lat, longitude=args.lon,maxradius=args.radius,
            mindepth=args.min_dep, maxdepth=args.max_dep)
except FDSNNoDataException:
    sys.exit('No events within given constraints.')

for eve in cat:
    # Get focal mechanisms.
    event_id = str(eve.preferred_origin_id).split('/')[4]
    ev = get_event_by_id(event_id)
    print("EVENT ID: {}".format(event_id))
    try:
        mt = ev.getProducts('moment-tensor')[0]
        qml = mt.getContentURL('quakeml.xml')
        ev = read_events(qml)[0]
        nps = ev.focal_mechanisms[0].nodal_planes
    except AttributeError:
        nps = 0
    # Print event information.
    timestring = eve.origins[0].time.strftime("%Y-%m-%d %H:%M:%S")
    locstring = "Lat: {:.2f}, Lon: {:.2f}, Depth: {:.2f}".format(
            eve.origins[0].latitude, eve.origins[0].longitude,
            eve.origins[0].depth/1000)
    if nps:
        magstring = "Magnitude: {:.2f} {}\nNodal Planes (S, D, R): ({},{},{}), ({},{},{})".format(
                eve.magnitudes[0].mag, eve.magnitudes[0].magnitude_type,
                nps.nodal_plane_1.strike, nps.nodal_plane_1.dip,
                nps.nodal_plane_1.rake, nps.nodal_plane_2.strike,
                nps.nodal_plane_2.dip, nps.nodal_plane_2.rake)
    else:
        magstring = "Magnitude: {:.2f} {}".format(
                eve.magnitudes[0].mag, eve.magnitudes[0].magnitude_type)
    print("{} {} \n{}\n".format(timestring, locstring, magstring))

# Plot events.
if args.plot:
    if args.radius <= 20:
        projection = 'local'
    elif args.radius > 20 and args.radius < 90:
        projection = 'ortho'
    else:
        projection = 'global'
    cat.plot(projection=projection)
