import tkinter as tk
from datetime import datetime
from datetime import timedelta
import pandas
from meteostat import Stations, Daily, Hourly
from geopy.geocoders import Nominatim

from scipy.ndimage.filters import gaussian_filter1d
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot

# calls root, sets up global variables
root = tk.Tk()
pandas.set_option("display.max_rows", None, "display.max_columns", None)

def Popup(message):# makes popup to tell user what is correct formatting
    #make a new window
    popup = tk.Tk()
    #gives window title (top bar)
    popup.wm_title("!")
    #make a label
    label = tk.Label(popup, text=message, font=("Helvetica", 10))
    #put it on screen
    label.pack(side="top", fill="x", pady=10)
    #make a button that destroys the popup
    B1 = tk.Button(popup, text="Okay", command=popup.destroy)
    #put the button on screen
    B1.pack()
    #mainloop it
    popup.mainloop()

def CreateObjects():# creates all the stuff for the first input box
    # labels the input box
    modeswitcherlabel = tk.Label(root, padx=20, pady=10, text="Input a city name or coordinates")
    #put the label on screen
    modeswitcherlabel.pack()
    # the actual input box
    inputbox = tk.Entry(root)
    #put the box on screen
    inputbox.pack()
    # the search button, calls "Search"
    searchbutton = tk.Button(root, text="search", padx=10, pady=5, command=lambda: Search(inputbox.get()))
    #put the button on screen
    searchbutton.pack()

def Search(input):# searches for location, called by searchbutton
    try:#if the location is valid
        #start a geolocator
        geolocator = Nominatim(user_agent="climate change visualizer")
        #get location
        location = geolocator.geocode(input)
    except BaseException:#if it is invalid
        #make a popup
        Popup("not a real city name")
        return
    #go to the FindClimateData function
    FindClimateData(location.latitude, location.longitude)

def GetStart(RawStart):# gets the start date
    #gets year
    year = RawStart[11] + RawStart[12] + RawStart[13] + RawStart[14]
    #gets month
    month = RawStart[16] + RawStart[17]
    #gets day
    day = RawStart[19] + RawStart[20]
    #returns them all as integers
    return datetime(int(year), int(month), int(day))

def PullData(currentday, station):# pulls data
    #initializes variables
    years = []
    totalweatherdata = []
    while currentday < (datetime.today() - timedelta(days=365.2422)): #while day being scanned is before this day last year
        #add a year to the current day to be scanned
        currentday += timedelta(days=365.2422)
        #get the daily data
        datatoadd = Daily(station, currentday - timedelta(days=365.2422), currentday).fetch().mean().get("tmax")
        if datatoadd != datatoadd or datatoadd == None:# if the datatoadd is NaN
            #try to get a replacement temperature
            datatoadd = Hourly(station, currentday - timedelta(days=365.2422), currentday).fetch().mean().get("temp")
        #add the new data to the plotting lists
        years.append(currentday.strftime("%Y"))
        #add the data to the list
        totalweatherdata.append(datatoadd)
    return totalweatherdata, years

def FindClimateData(latitude, longitude):# Finds climate data based on Lat and Long
    #get a station
    station = Stations().nearby(latitude, longitude).inventory("hourly", datetime(1950, 1, 1)).fetch(1)
    #get the first day the station was on
    firststationday = GetStart(str(station.get("hourly_start")))
    #pull the data
    totalweatherdata, years = PullData(firststationday, station)
    #set a raw Y value
    rawy = totalweatherdata
    #smooth out the Y axis data
    ysmoothed = gaussian_filter1d(totalweatherdata, sigma=3)
    #plot and show it
    Infopage(years, ysmoothed, rawy, latitude, longitude)

def Infopage(years, ysmoothed, rawy, latitude, longitude):# makes the page to display info
    #starts the infopage
    infopage = tk.Tk()
    #makes a figure
    figure = Figure(figsize=(10, 8), dpi=100)
    #adds something?
    plot = figure.add_subplot(1, 1, 1)
    #makes the plot a tkinter widget
    canvas = FigureCanvasTkAgg(figure, infopage)
    #plots the data
    plot.plot(years, ysmoothed, label="smoothed data")
    plot.plot(years, rawy, label="raw data")
    #label the axes
    pyplot.xlabel("years")
    pyplot.xlabel("avg. temp (C)")
    #puts the widget in the infopage
    canvas.get_tk_widget().grid(row=0, column=0)
    #sets the ticks on bottom to 10
    plot.xaxis.set_major_locator(pyplot.MaxNLocator(15))
    #start a geolocator to give exact location of weather station
    geolocator = Nominatim(user_agent="climate change visualizer")
    #make the label
    infolabel = tk.Label(infopage, pady=30, padx=10, width=100, text="Y axis does not start from 0.\n"
    "X axis ends at the current year. Orange line is raw yearly average, blue is smoothed\nBroken lines show a break in the weatherkeeping records. Try a larger city if this issue is too bad\n\n"
    "\nExact location of weather station: " + geolocator.reverse(str(latitude) + ",  " + str(longitude)).raw["address"]["city"])
    #set the font
    infolabel.configure(font=("Calibri", 12))
    #put the label in
    infolabel.grid(row=1, column=0)
    #mainloop it
    infopage.mainloop()

#start the program
CreateObjects()
#mainloop it
root.mainloop()