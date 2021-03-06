# -*- coding: utf-8 -*-
from flask import Flask, request, render_template, redirect, url_for, flash
from flask import abort
from werkzeug import secure_filename
from flask_bootstrap import Bootstrap
import os
import csv
import errno
import json
import re
## import psycopg2 as psy
from functools import wraps
from ewaim import *
## from static.py.db_util import *

############################################################
############################################################
############################################################

## Init the app

UPLOAD_FOLDER = '/tmp/'
app = Flask(__name__)
Bootstrap(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
SECRET_KEY = "stars_and_moon"
DEBUG = True
app.config.from_object(__name__)

## Utility functions
def makePathExist(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

makePathExist('static/db')

############################################################
############################################################
############################################################

## Setup Middleware / routes to each web page

#get species names and metadata

spstat = {}
splist = []
handle = open('./static/csv/pearl_data_summary_full.csv')
for line in handle:
    data = line.strip().split(',')
    id, sn, clade, iucn, quality, certainty, source, ln, pn, tss, auc, tssr, aucr = data
    if type(tss) == float:
        tss = round(tss,2)
    if type(auc) == float:
        auc = round(auc,2)
    spstat[pn] =  [clade, source, tss, auc, quality, certainty, iucn] #order
    pn2 = pn.replace('_',' ')
    splist.append(pn2)

splist = splist[1::]
handle.close()

@app.route("/about", methods = ["GET", "POST"])
def about():
    return render_template("about.html")

@app.route("/pub",methods = ["GET","POST"])
def pub():
    return render_template("pub.html")

@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST":
        print("\n------")
        print("POST request in index")
        print("------\n")

        if request.form['searchbar']:
            try:
                req_raw = request.form['searchbar'] #change all values in index.html into species names instead of abbrreviation
                if req_raw == "foo_sp":
                    flash("Please pick a species to render the map page.")
                    return redirect(request.url)

                req_raw = req_raw.lower()
                init_zoom = 3
                init_lat = 42.9077121476637
                init_long = -103.78906354308131
                data_name = "Global Parasite Distributions"
                pearl_sp = req_raw.replace(' ','_')
                pearl_sp2 = pearl_sp.capitalize()
                prop_name = req_raw.capitalize()
                sub_name = ""
                obj_show = {
                    "pearl_sp" : pearl_sp,
                    "prop_name" : prop_name,
                    "sub_name" : sub_name,
                    "data_name" : data_name,
                    "init_zoom" : init_zoom,
                    "init_lat" : init_lat,
                    "init_long" : init_long,
                    "clade" : spstat[pearl_sp2][0],
                    "source" : spstat[pearl_sp2][1],
                    "tss" : spstat[pearl_sp2][2],
                    "auc" : spstat[pearl_sp2][3],
                    "quality" : spstat[pearl_sp2][4],
                    "certainty" : spstat[pearl_sp2][5],
                    "iucn" : spstat[pearl_sp2][6]
                }

                spfilename = req_raw.upper().replace(' ','_')
                pathName = "./static/csv/pearl_sp/" + spfilename + "_pearldata.csv"
                obj_sp = get_csv(csv_path = pathName)

                return render_template("pearl_map.html", obj_show = obj_show, obj_sp = obj_sp, splist = splist)

            except:
                flash("Bad query - could not interpret.")
                return redirect(request.url)

    return render_template("index.html", splist = splist)

@app.route("/pearl_map", methods = ["GET", "POST"])
def pearl_map():
    if request.method == "POST":
        print("\n------")
        print("POST request in pearl_map")
        print("------\n")

        if request.form['searchbar']:

            try:
                req_raw = request.form['searchbar'] #change all values in index.html into species names instead of abbrreviation

                if req_raw == "foo_sp":
                    flash("Please pick a species to render the map page.")
                    return redirect(request.url)

                req_raw = req_raw.lower()
                init_zoom = 3
                init_lat = 11.252725743861603
                init_long = -0.005242086131886481
                data_name = "Global Parasite Distributions"
                pearl_sp = req_raw.replace(' ','_')
                prop_name = req_raw.capitalize()
                sub_name = ""
                obj_show = {
                    "pearl_sp" : pearl_sp,
                    "prop_name" : prop_name,
                    "sub_name" : sub_name,
                    "data_name" : data_name,
                    "init_zoom" : init_zoom,
                    "init_lat" : init_lat,
                    "init_long" : init_long
                }
                spfilename = req_raw.upper().replace(' ','_')
                pathName = "./static/csv/pearl_sp/" + spfilename + "_pearldata.csv"
                obj_sp = get_csv(csv_path = pathName)
                return render_template("pearl_map.html", obj_show = obj_show, obj_sp = obj_sp, splist = splist)

            except:
                flash("Bad query - could not interpret.")
                return redirect(request.url)

    return render_template("pearl_map.html", splist = splist)

@app.route("/<pedon_key>/")
def point_page(pedon_key):
    obj_list = get_csv()
    for row in obj_list:
        if row['pedon_key'] == pedon_key:
            return render_template("point_page.html", obj_row = row)

    abort(404)

@app.route("/show_calc", methods = ["GET", "POST"])
def show_calc():
    return render_template("show_calc.html")

@app.route("/get_calc", methods = ["GET", "POST"])
def get_calc():

    if request.method == "POST":
        if ((request.form['query_string'] is None) or (len(request.form['query_string']) == 0)):
            flash("Bad query - could not interpret.")
            return redirect(request.url)

        if request.form['query_string']:

            try:
                simple_math = request.form['query_string']
                calc_result = calculate(simple_math)
                return render_template("show_calc.html", simple_math = simple_math, calc_result = calc_result)
            except:
                flash("Something went wrong...")
                return redirect(request.url)

    return render_template("get_calc.html")


######## Below route as reference (may use)

@app.route("/ex_raster", methods = ["GET", "POST"])
def ex_raster():
    return render_template("ex_tif_raster.html")

# Creeate route for fileupload html
@app.route("/file_upload", methods = ["GET", "POST"])
def file_upload():
    if request.method == "POST":
        if len(request.files) > 0:

            flash("Successfully uploaded BibTeX file")
            fileStruct = request.files['fileInput']

            # check if the post request has the file part
            if 'fileInput' not in request.files:
                flash('No file part')
                return redirect(request.url)

            # if user does not select file, browser also
            # submit a empty part without filename
            if fileStruct.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if fileStruct.filename:
                filename = secure_filename(fileStruct.filename)
                fileStruct.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Add Bib file to relative path
                absPathh = os.path.abspath(UPLOAD_FOLDER + filename)
                bibDB = bib_parse(absPathh)

                if "collectName" in request.form:
                    if (request.form["collectName"] == '') or (len(request.form["collectName"]) == 0):
                        collectName = "Default"
                    else:
                        collectName = request.form["collectName"]
                else:
                    collectName = "Default"

                # Create table and pass in collection name
                create_table(collectName, bibDB)

                return render_template("show_results.html", collectName = collectName, filenamee = filename, fileUpload = bibDB[0], fileSize = len(bibDB))

        else:
            # No file uploaded
            flash("Please select a file and try again.")
            return redirect(request.url)

    return render_template("file_upload.html")

# Creeate route for show_results html
@app.route("/show_results", methods = ["GET", "POST"])
def show_results():
    return render_template("show_results.html")

if __name__ == "__main__":
    ## app.run(port = 5051, debug = True, use_reloader = True)
    app.run(host='0.0.0.0', port=5051)
