# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

import os

#allow overrides
arcpy.env.overwriteOutput = True
#%%
#define the location where the georeferenced strips are using a while true loop
#this allows the script to continue collecting inputs until the criteria is met without giving an error and ending the script run
#if the strip location input path does not include .gdb, it is incorrect and will prompt the user to input another path name

while True:
    try:
        striploc = raw_input("Enter the full file path for the geodatabase which contains all of the georeferenced strips you would like to include in the mosaic. Nothing else should be in the geodatabase. >> ")
        if ".gdb" in striploc:
            break
        else:
            print "Invalid entry. Make sure to include the full file path including the .gdb extension."
            continue
    except ValueError:
        print("Ivalid entry. Make sure to include the full file path including the .gdb extension.")
        continue

#%%
#define the location where a geodatabase will be created for strip outputs
#same as for strip location, only this time, the only requirement is to include :\ which just filters for other strings or inputs that don't include a path

while True:
    try:
        makeGDBloc = raw_input("Enter the location where you would like to store the geodatabase that is required to run this code >> ")
        if ":\\" in makeGDBloc:
            break
        else:
            print "Invalid entry. Make sure to include the full file path."
            continue
    except ValueError:
        print("Invalid entry. Make sure to include the full file path.")

#%%
#define the location where the final mosaic will be stored
#same as for makeGDBloc
while True:
    try:
        mosaicloc = raw_input("Enter the full file path for the folder where you would like to output the final mosaic to (not within a geodatabase) >> ")
        if ":\\" in mosaicloc:
            break
        else:
            print "Invalid entry. Make sure to include the full file path."
            continue
    except ValueError:
        print("Invalid entry. Make sure to include the full file path.")

#use output location specified above to join to a full path name for the final mosaic, which will be used at the end of the script to copy the mosaic dataset to the specified location
finalmosaic = os.path.join(mosaicloc, "FinalMosaic.tif")

#%%
#define output cell size of the final mosaic
#if user inputs anything other than an interger or float number greater than zero, they have to retry.
while True:
    try:
        cellsize = float(raw_input("Enter the desired output cell size for the final mosaic in number format (i.e. 2.5) >> "))
        if cellsize > 0:
            break
        else:
            print "Invalid entry. Make sure to enter a number as an integar or float (i.e. 2, 2.5, 2.55, etc)"
    except ValueError:
        print "Invalid entry. Make sure to enter a number as an integar or float (i.e. 2, 2.5, 2.55, etc.)"

#%%
#define the clipping geometry for the mosaic, which is the study area
#if the user does not enter the full path name including the .shp file type for the shapefile, they have to retry.
while True:
    try:
        aoi_bounds = raw_input("Enter the full file path for the shapefile you would like to clip the mosaic to (.shp format only) >> ")
        if ".shp" in aoi_bounds:
            break
        else:
            print "Invalid entry. Make sure to include the full file path including the .shp extension."
            continue
    except ValueError:
        print "Invalid entry. Make sure to include the full file path including the .shp extension."

#%%
#define the coordinate system for the strips and mosaic (UTM preferred, based on location of strips)
while True:
    try:
        coordinate_system = raw_input("Enter the well-known ID (WKID) for the coordinate system you would like to use for mosaicing (should match the coordinate system of your georeferenced strips) >> ")
        #get the string length of the user input
        coord_length = len(coordinate_system)
        #all of the well-known IDs are at least 4 numbers in length, so this will weed out any potential errors
        if coord_length >= 4:
            break
        else:
            print "Invalid entry. Please input the well-known ID for the desired coordinate system (usually a four, five, or six digit number)."
            continue
    except ValueError:
        print "Invalid entry. Please input the well-known ID for the desired coordinate system (usually a four, five, or six digit number)."
#%%
print "The mosaicing process will begin now. You will receive a message when it is complete."

#%% create a new file geodatabase where code outputs will be stored and create an empty mosaic dataset within it

#set workspace to path identified previously as GDB location
arcpy.env.scratchWorkspace = makeGDBloc
arcpy.env.workspace = makeGDBloc

#create the the file geodatabase at the previously specified location
arcpy.CreateFileGDB_management(makeGDBloc, "CoronaMosaicGDB.gdb")

#use os join path to create a variable to easily access the GDB location
mosaicGDB = os.path.join(makeGDBloc, "CoronaMosaicGDB.gdb")

#create the empty mosaic dataset within the newly created file geodatabase
arcpy.CreateMosaicDataset_management(mosaicGDB, "CoronaMosaic", coordinate_system, "1", "8_BIT_UNSIGNED", "NONE", "")

#ose os join path to create a variable to easily access the mosaic dataset location
mosaic = os.path.join(mosaicGDB, "CoronaMosaic")

#%% generate a list of input strips based on strip location identified previously

#set workspace to location of georeferenced strips in file GDB
arcpy.env.workspace = striploc

#create list variable that stores the file paths for each of the georeferenced strips as a list element
striplist = arcpy.ListRasters("*", "GRID")

#print a list of the strips appended to the list
print "The following strips will be used to create the mosaic: "
print striplist

#%%PREPARE STRIPS FOR MOSAIC AND ADD THEM TO THE MOSAIC DATASET

#the georeferencing process often skews raster grids and changes cell sizes
#clipping strips by the AOI bounds at this stage is faster than clipping the end mosaic later

#iterate through the list of strips- resample and clip each one
for strip in striplist:
    #create naming mechanism for resampled version of each strip
    outRSname = arcpy.Describe(strip).baseName + "_RS"

    #create naming mechanism for clipped version of each resampled strip
    outclipname = arcpy.Describe(strip).baseName + "_RS_clip" # Creates a new output name

    #use arcpy resample to intake strip and resample to the specified cell cize using bilinear resampling method (important to preserve clarity of image)
    arcpy.Resample_management(strip, outRSname, cellsize, "BILINEAR")

    #use arcpy clip to intake resampled strip and clip it to the specified AOI.
    arcpy.Clip_management(outRSname, "", outclipname, aoi_bounds, "256", "ClippingGeometry", "NO_MAINTAIN_EXTENT")

    #add the resampled and clipped strip to the mosaic dataset created prior
    arcpy.AddRastersToMosaicDataset_management(mosaic, "Raster Dataset", outclipname, "UPDATE_CELL_SIZES", "UPDATE_BOUNDARY", "NO_OVERVIEWS", "", "0", "1500", "", "", "SUBFOLDERS", "OVERWRITE_DUPLICATES", "BUILD_PYRAMIDS", "CALCULATE_STATISTICS", "NO_THUMBNAILS", "", "NO_FORCE_SPATIAL_REFERENCE", "ESTIMATE_STATISTICS", "")

    print "%s has been resampled, clipped, and added to the mosaic dataset" %strip

#%%COLOR BALANCE THE MOSAIC AND GENERATE SEAMLINES TO SMOOTH EDGES BETWEEN STRIPS

arcpy.management.ColorBalanceMosaicDataset(in_mosaic_dataset = mosaic, balancing_method = "HISTOGRAM")

arcpy.BuildSeamlines_management(in_mosaic_dataset=mosaic, sort_method="CLOSEST_TO_VIEWPOINT", sort_order="DESCENDING", order_by_attribute="", view_point="", computation_method="RADIOMETRY")
#%%COPY FINAL MOSAIC TO .TIF FORMAT

arcpy.CopyRaster_management(mosaic, finalmosaic, "", "", "256", "NONE", "NONE", "", "NONE", "NONE", "TIFF", "NONE")

print "The mosaic is complete. It can be found at the following location: "
print finalmosaic
