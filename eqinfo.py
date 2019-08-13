#!/usr/bin/env python
from obspy import UTCDateTime, Stream, read_events
from obspy.clients.fdsn import Client
from libcomcat.search import search, get_event_by_id
import argparse

parser = argparse.ArgumentParser(description='Get Earthquake Information')

parser.add_argument("-p", action="store_true", dest="plot",
        default=False, required=False, help='Plot events')

parser.add_argument("-s", "--stime", action="store", dest="stime",
        default=False, type=str, required = True,
        help="start time for search window, i.e. YYYY-DDD hh:mm:ss")

parser.add_argument("-e", "--etime", action="store", dest="etime",
        default=False, type=str, required=False,
        help="end time for search window, Will accept any UTCDateTime format")

# alternative option to -e
parser.add_argument("-n", "--number", action="store", dest="number",
        default=False, type=float, help="number of days since start time")

parser.add_argument("-mM", action="store", dest="min_mag", required=False,
        default=2.5, type=float, help="minimum magnitude")

parser.add_argument("-MM", action="store", dest="max_mag", required=False,
        default=9.9, type=float, help="maximum magnitude")

parser.add_argument("-md", action="store", dest="min_dep", required=False,
        default=0, type=float, help="minimum depth")

parser.add_argument("-Md", action="store", dest="max_dep", required=False,
        default=1000, type=float, help="maximum depth in km")

parser.add_argument("-l", "--lat", action="store", dest="lat", default=0.0,
        required=False, type=float, help="latitude for search radius")

parser.add_argument("-L", "--lon", action="store", dest="lon", default=0.0,
        required=False, type=float, help="longitude for search radius")

parser.add_argument("-r", "--radius", action="store", dest="radius",
        default=180, required=False, type=float, help="event search radius")

args = parser.parse_args()

# set timing
try:
    stime = UTCDateTime(args.stime)
except:
    sys.exit("Must provide a start time for search window using -st option")

if args.etime:
    etime = UTCDateTime(args.etime)
elif args.number:
    etime = stime + 86400 * args.number
else:
    etime = UTCDateTime()
    print("No end time or # of days provided. Using current time as end time")

client = Client('USGS')
try:
    cat = client.get_events(starttime=stime, endtime=etime,
            minmagnitude=args.min_mag, maxmagnitude=args.max_mag,
            latitude=args.lat, longitude=args.lon,maxradius=args.radius,
            mindepth=args.min_dep, maxdepth=args.max_dep)
except:
    sys.exit('No events available')

for eve in cat:
    event_id = str(eve.preferred_origin_id).split('/')[4]
    ev = get_event_by_id(event_id)
    mt = ev.getProducts('moment-tensor')[0]
    qml = mt.getContentURL('quakeml.xml')
    ev = read_events(qml)[0]
    nps = ev.focal_mechanisms[0].nodal_planes
    timestring = str(eve.origins[0].time).split('T')
    timestring = "Time: {} {}".format(timestring[0],
            timestring[1].split('.')[0])
    locstring = "Lat: {:.2f}, Lon: {:.2f}, Depth: {:.2f}".format(
            eve.origins[0].latitude, eve.origins[0].longitude,
            eve.origins[0].depth/1000)
    try:
        magstring = "Magnitude: {:.2f} {}\nNodal Planes (S, D, R): ({},{},{}) \
                ({},{},{})".format(eve.magnitudes[0].mag,
                eve.magnitudes[0].magnitude_type,
                nps.nodal_plane_1.strike, nps.nodal_plane_1.dip,
                nps.nodal_plane_1.rake, nps.nodal_plane_2.strike,
                nps.nodal_plane_2.dip, nps.nodal_plane_2.rake)
    except:
        magstring = "Magnitude: {:.2f} {}".format(
                eve.magnitudes[0].mag, eve.magnitudes[0].magnitude_type)
    print("EVENT ID: {}\n{} {} \n{}\n".format(event_id, timestring,
            locstring, magstring))


#lats = [eve.origins[0].latitude for eve in cat]
#lons = [eve.origins[0].longitude for eve in cat]
#deps = [eve.origins[0].depth for eve in cat]
#mags = [eve.magnitudes[0].mag for eve in cat]

if args.plot:
    cat.plot(projection='local')
