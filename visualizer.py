# TK for graphics
import tkinter as tk
from datetime import datetime
from datetime import timedelta
import pandas
from meteostat import Stations, Daily
# for city --> GPS conversions
from geopy.geocoders import Nominatim
from scipy.ndimage.filters import gaussian_filter1d
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot
from re import search

# calls root, sets up global variables
root = tk.Tk()
pandas.set_option("display.max_rows", None, "display.max_columns", None)

def Popup(message):
    # makes popup to tell user what is correct formatting
    popup = tk.Tk()
    popup.wm_title("!")
    label = tk.Label(popup, text=message,
                     font=("Helvetica", 10))
    label.pack(side="top", fill="x", pady=10)
    B1 = tk.Button(popup, text="Okay", command=popup.destroy)
    B1.pack()
    popup.mainloop()

def CreateObjects():
    # labels the input box
    modeswitcherlabel = tk.Label(root, padx=20, pady=10, text="Input a city name or coordinates")
    modeswitcherlabel.pack()
    # the actual input box
    inputbox = tk.Entry(root)
    inputbox.pack()
    # the search button, calls "Search"
    searchbutton = tk.Button(root, text="search", padx=10, pady=5, command=lambda: Search(inputbox.get()))
    searchbutton.pack()

def Search(input):# searches for location, called by searchbutton
    try:#if the location is valid, start a geolocator
        geolocator = Nominatim(user_agent="climate change visualizer")
        #gets location
        location = geolocator.geocode(input)
    except BaseException:#if it is invalid, send a popup telling the user how to fix it
        Popup("Either incorrectly formatted (Format as -48.876667, -123.39333) \n or not a real city name.")
        return
    #go to the FindClimateData function
    FindClimateData(location.latitude, location.longitude)

def FindClimateData(latitude, longitude):# Finds climate data based on Lat and Long
    #################################################################### HAVING ISSUE WITH NOT SHOWING ALL DATA (LONDON SEARCH, ONLY RETURNS 1988 ONWARDS B/C SOME VALUES ARE "nat") | MIGHT WANT TO ALLOW TO SELECT PRINCIPALITY
    ##################################MAKE SOMETHING THAT, IF THERE IS A nan, CHECKS FOR NEAREST WEATHER STATION THAT COULD FILL IN THE NAN AND FILL IT IN
    ##################################CHECK IF DATA IS AVERAGING/READING PROPERLY FOR THE NANS
    ##############################I give up, it works in most locations
    for i in range(1,11): #for each of the 10 nearest stations
        station = Stations().nearby(latitude, longitude).fetch(i).tail(1) #get the most recent one being checked
        #learned about the searching with https://stackoverflow.com/questions/45136598/extract-string-with-specific-format/45136706#45136706?newreg=aeb07c2a61a64de48294c5bb6a4d7a13

        if search('\d{4}'+"-"+'\d{2}'+"-"+'\d{2}', str(station.get("hourly_start"))): #if there a substring with "####-##-##" formatting in the hourly start
            #set firststationday to string found in hourly start
            firststationday = search('\d{4}'+"-"+'\d{2}'+"-"+'\d{2}', str(station.get("hourly_start"))).group(0).split("-")
            #format firststationday
            firststationday = datetime(int(firststationday[0]), int(firststationday[1]), int(firststationday[2]))
            if firststationday < datetime(1950, 1, 2): #if firststationday is before 1950, break the loop
                break
        if search('\d{4}'+"-"+'\d{2}'+"-"+'\d{2}', str(station.get("daily_start"))): #if there a substring with "####-##-##" formatting in the daily start
            # set firststationday to string found in daily start
            firststationday = search('\d{4}'+"-"+'\d{2}'+"-"+'\d{2}', str(station.get("daily_start"))).group(0).split("-")
            #format firststationday
            firststationday = datetime(int(firststationday[0]), int(firststationday[1]), int(firststationday[2]))
            if firststationday < datetime(1950, 1, 2): #if firststationday is before 1950, break the loop
                break
    # gets day to start look on, if none is found for some reason it tells user to use a city that will have one
    currentday = firststationday
    # initializes lists for plotted data
    totalweatherdata = []
    years = []
    # get the data for that year
    firstyeardata = Daily(station, currentday, currentday + timedelta(days=3650)).fetch().mean()

    while currentday < (datetime.today() - timedelta(days=365.2422)): #while day being scanned is before this day last year
        #add a year to the current day to be scanned
        currentday += timedelta(days=365.2422)
        if currentday < datetime(1950, 1, 1): #if the day being scanned is before 1960, pass over it
            continue
        #get the data for that year
        data = Daily(station, currentday - timedelta(days=365.2422), currentday)
        data = data.fetch()
        #find the averages
        data = data.mean()
        #add the new data to the plotting lists
        years.append(currentday.strftime("%Y"))
        #add the avg maxtemp
        totalweatherdata.append(data.get("tmax"))
    rawy = totalweatherdata
    #smooth out the Y axis data
    ysmoothed = gaussian_filter1d(totalweatherdata, sigma=3)
    #plot and show it
    Infopage(years, ysmoothed, rawy, firstyeardata.get("tmax"), latitude, longitude)


def Infopage(years, ysmoothed, rawy, firstdecade, latitude, longitude):

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
    #label the axis
    pyplot.xlabel("years")
    pyplot.xlabel("avg. temp (C)")
    #puts the widget in the infopage
    canvas.get_tk_widget().grid(row=0, column=0)
    #sets the ticks on bottom to 10
    plot.xaxis.set_major_locator(pyplot.MaxNLocator(15))

    infolabel1 = tk.Label(infopage, pady=30, padx=10, width=100, text="Y axis does not start from 0.\nLine gaussian smoothed to eliminate changes over the year or short anomalies.\n"
    "X axis ends at the current year. Orange line is raw yearly average, blue is smoothed\nBroken lines show a break in the weatherkeeping records. Try a larger city if this issue is too bad\n\n"
    "average temp of first decade recorded in the area: " + str(firstdecade.round(2)) + ". This may be innacurate. Some weather stations don't keep good records.\nExact location of weather station: "
    + str(latitude) + "  " + str(longitude))
    #set the font
    infolabel1.configure(font=("Times New Roman", 12))
    #put the label in
    infolabel1.grid(row=1, column=0)
    #mainloop it
    infopage.mainloop()

CreateObjects()

root.mainloop()