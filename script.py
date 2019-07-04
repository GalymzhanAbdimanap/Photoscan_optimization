# Auto batch process for Agisoft PhotoScan
# 27/06/19

import PhotoScan
import os,re,sys
import sqlite3
import time, datetime
from datetime import datetime
conn = sqlite3.connect("/home/manapov/Downloads/Agisoft_photoscan_pro/photoscan-pro/db.db")
#c = conn.cursor()
#upload_path = '/home/jalal/3dmodeling'
upload_path = '/home/manapov/3dmodeling'
data = 'mod_pcloud'




# get the photo (.JPG) list in specified folder
def getPhotoList(root_path, photoList):
	pattern = '.JPG$'
	for root, dirs, files in os.walk(root_path):
		for name in files:
			if re.search(pattern,name):
				cur_path = os.path.join(root, name)
				#print (cur_path)
				photoList.append(cur_path)
			
def PhotoScanProcess(root_path, t_id):				
	#PhotoScan.app.messageBox('hello world! \n')
	PhotoScan.app.console.clear()

	print(root_path, t_id)
	doc = PhotoScan.app.document

	## save project
	#doc.open("M:/PhotoScan/practise.psx")
	#psxfile = root_path + 'practise.psx'
	#doc.save( psxfile )
	#print ('>> Saved to: ' + psxfile)

	## point to current chunk
	#chunk = doc.chunk

	## add a new chunk
	chunk = doc.addChunk()

	## set coordinate system
	# - PhotoScan.CoordinateSystem("EPSG::4612") -->  JGD2000
	chunk.crs = PhotoScan.CoordinateSystem("EPSG::4612")

	################################################################################################
	### get photo list ###
	photoList = []
	getPhotoList(root_path, photoList)
	#print (photoList)
	
	################################################################################################
	### add photos ###
	# addPhotos(filenames[, progress])
	# - filenames(list of string) – A list of file paths.
	chunk.addPhotos(photoList)
	
	################################################################################################
	### align photos ###
	## Perform image matching for the chunk frame.
	# matchPhotos(accuracy=HighAccuracy, preselection=NoPreselection, filter_mask=False, keypoint_limit=40000, tiepoint_limit=4000[, progress])
	# - Alignment accuracy in [HighestAccuracy, HighAccuracy, MediumAccuracy, LowAccuracy, LowestAccuracy]
	# - Image pair preselection in [ReferencePreselection, GenericPreselection, NoPreselection]
	chunk.matchPhotos(accuracy=PhotoScan.HighAccuracy, preselection=PhotoScan.GenericPreselection, filter_mask=False, keypoint_limit=40000, tiepoint_limit=4000)
	chunk.alignCameras()

	################################################################################################
	### build dense cloud ###
	## Generate depth maps for the chunk.
	# buildDenseCloud(quality=MediumQuality, filter=AggressiveFiltering[, cameras], keep_depth=False, reuse_depth=False[, progress])
	# - Dense point cloud quality in [UltraQuality, HighQuality, MediumQuality, LowQuality, LowestQuality]
	# - Depth filtering mode in [AggressiveFiltering, ModerateFiltering, MildFiltering, NoFiltering]
	chunk.buildDepthMaps(quality=PhotoScan.MediumQuality, filter=PhotoScan.MildFiltering)
	chunk.buildDenseCloud(point_colors = True)

	################################################################################################
	### build mesh ###
	## Generate model for the chunk frame.
	# buildModel(surface=Arbitrary, interpolation=EnabledInterpolation, face_count=MediumFaceCount[, source ][, classes][, progress])
	# - Surface type in [Arbitrary, HeightField]
	# - Interpolation mode in [EnabledInterpolation, DisabledInterpolation, Extrapolated]
	chunk.buildModel(surface=PhotoScan.Arbitrary, interpolation=PhotoScan.EnabledInterpolation, face_count=PhotoScan.HighFaceCount)
	chunk.model.closeHoles()
	chunk.buildUV(mapping=PhotoScan.GenericMapping)
	
	chunk.buildTexture(blending=PhotoScan.MosaicBlending, size=2048, fill_holes=True, ghosting_filter=True)
	model_path = os.path.join(upload_path, project_name, data) + '/model.obj'
	points_path = os.path.join(upload_path, project_name, data) + '/points_cloud.obj'
	chunk.exportPoints(path = points_path, binary=False, format=PhotoScan.PointsFormatOBJ, normals=True, colors=True, precision=6)
	chunk.exportModel(path = model_path, binary=False, precision=6, texture_format=PhotoScan.ImageFormatJPEG, normals=True, colors=True, cameras = False, udim = False, strip_extensions = False, format=PhotoScan.ModelFormatOBJ)
	print(model_path)
	print("-----------------------------------------------------")
	conn.execute('UPDATE tasks SET Status = "Complete" WHERE id=?', (t_id,))
	conn.commit()
	print('Status: Complete')
	#conn.close()
	# - Blending mode in [AverageBlending, MosaicBlending, MinBlending, MaxBlending, DisabledBlending]
	#chunk.buildTexture(blending=PhotoScan.MosaicBlending, color_correction=True, size=30000)

	################################################################################################
	## save the project before build the DEM and Ortho images
    #
    #

    
    #


    #
    #
    
    
	#doc.save()

	################################################################################################
	### build DEM (before build dem, you need to save the project into psx) ###
	## Build elevation model for the chunk.
	# buildDem(source=DenseCloudData, interpolation=EnabledInterpolation[, projection ][, region ][, classes][, progress])
	# - Data source in [PointCloudData, DenseCloudData, ModelData, ElevationData]
	#chunk.buildDem(source=PhotoScan.DenseCloudData, interpolation=PhotoScan.EnabledInterpolation, projection=chunk.crs)

	################################################################################################
	## Build orthomosaic for the chunk.
	# buildOrthomosaic(surface=ElevationData, blending=MosaicBlending, color_correction=False[, projection ][, region ][, dx ][, dy ][, progress])
	# - Data source in [PointCloudData, DenseCloudData, ModelData, ElevationData]
	# - Blending mode in [AverageBlending, MosaicBlending, MinBlending, MaxBlending, DisabledBlending]
	#chunk.buildOrthomosaic(surface=PhotoScan.ModelData, blending=PhotoScan.MosaicBlending, color_correction=True, projection=chunk.crs)
	
	################################################################################################
	## auto classify ground points (optional)
	#chunk.dense_cloud.classifyGroundPoints()
	#chunk.buildDem(source=PhotoScan.DenseCloudData, classes=[2])
	
	################################################################################################
	#doc.save()

project_name = conn.execute('SELECT id, ProjectPath FROM tasks where Pid is NULL ')
project_name = project_name.fetchone()
#print(project_name)
project_id = project_name[0]
project_name = project_name[1]
folder = os.path.join(upload_path, project_name, 'images')

project_path = os.path.join(upload_path, project_name, data)
if not os.path.exists(project_path):
            os.makedirs(project_path)
# Clear images dir
else:
	for the_file in os.listdir(project_path):
		file_path = os.path.join(project_path, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as e:
			print(e)
#folder = "/home/manapov/Downloads/10/images/"
PhotoScanProcess(folder, project_id)