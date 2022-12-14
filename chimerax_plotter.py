#!/usr/bin/env python

#############################################################################
######   This script is a python+julia script to conduct machine-learning
######   comparative analyses of two molecular dynamics trajectories
######   It is part of the DROIDS v6.0 ChimeraX plug-in suite for
######   machine-learning assisted comparative protein dynamics
######   produced by Dr. Gregory A. Babbitt and students at the 
######   Rochester Instituteof Technology in 2022.   License under GPL v3.0
#############################################################################

import getopt, sys # Allows for command line arguments
import os
import random as rnd
#import pytraj as pt
#import nglview as nv
from scipy.spatial import distance
from scipy.stats import entropy
from scipy.stats import ks_2samp
from sklearn.metrics.cluster import normalized_mutual_info_score
from sklearn.decomposition import TruncatedSVD
from sklearn import metrics
import re
# for ggplot
import pandas as pd
import numpy as np
import scipy as sp
from pandas.api.types import CategoricalDtype
from plotnine import *
#from plotnine.data import mpg



################################################################################
# READ CONTROL FORM
# read ChimeraX visualization ctl file
infile = open("DROIDS.ctl", "r")
infile_lines = infile.readlines()
for x in range(len(infile_lines)):
    infile_line = infile_lines[x]
    #print(infile_line)
    infile_line_array = str.split(infile_line, ",")
    header = infile_line_array[0]
    value = infile_line_array[1]
    #print(header)
    #print(value)
    if(header == "queryID"):
        query_id = value
        print("my query ID is",query_id)
    if(header == "referenceID"):
        ref_id = value
        print("my reference ID is",ref_id)
    if(header == "queryPDB"):
        query_pdb = value
        print("my query PDB is",query_pdb)
    if(header == "referencePDB"):
        ref_pdb = value
        print("my reference PDB is",ref_pdb)
    if(header == "queryTOP"):
        query_top = value
        print("my query TOP is",query_top)
    if(header == "referenceTOP"):
        ref_top = value
        print("my reference TOP is",ref_top)
    if(header == "queryTRAJ"):
        query_traj = value
        print("my query TRAJ is",query_traj)
    if(header == "referenceTRAJ"):
        ref_traj = value
        print("my reference TRAJ is",ref_traj)
    if(header == "subsamples"):
        sub_samples = value
        print("my subsamples is",sub_samples)   
    if(header == "frame_size"):
        fr_sz = value
        print("my frame size is",fr_sz)    
    if(header == "n_frames"):
        n_fr = value
        print("my number of frames is",n_fr)
    if(header == "num_chains"):
        n_ch = value
        print("my number of chains is",n_ch)
    if(header == "length"):
        l_pr = value
        print("my total protein length is",l_pr)    
    if(header == "chimerax"):
        ch_path = value
        print("my chimerax path is",ch_path)
    if(header == "bgcolor"):
        bg_color = value
        print("my background is",bg_color)    
    if(header == "divergence"):
        div_anal = value
        print("run divergence is",div_anal)    
    if(header == "discrepancy"):
        disc_anal = value
        print("run discrepancy is",disc_anal)
    if(header == "conservation"):
        cons_anal = value
        print("run conserved dynamics is",cons_anal)
    if(header == "coordination"):
        coord_anal = value
        print("run coordinated dynamics is",coord_anal)
    if(header == "variants"):
        var_anal = value
        print("run variant dynamics is",var_anal)
###### variable assignments ######
PDB_id_query = ""+query_id+""
PDB_id_reference = ""+ref_id+""
PDB_file_query = ""+query_pdb+""
PDB_file_reference = ""+ref_pdb+""
top_file_query = ""+query_top+""
top_file_reference = ""+ref_top+""
traj_file_query = ""+query_traj+""
traj_file_reference = ""+ref_traj+""
subsamples = int(sub_samples)
frame_size = int(fr_sz)
n_frames = int(n_fr)
num_chains = int(n_ch)
length_prot = int(l_pr)
chimerax_path = ""+ch_path+""
#chimerax_path = "/usr/lib/ucsf-chimerax/bin/"
graph_scheme = ""+bg_color+""
div_anal = ""+div_anal+""
disc_anal = ""+disc_anal+""
cons_anal = ""+cons_anal+""
coord_anal = ""+coord_anal+""
var_anal = ""+var_anal+""

# create folder for ChimeraX visualization files
if not os.path.exists('ChimeraXvis'):
           os.makedirs('ChimeraXvis')

#######################################################################
def resinfo():
    ### collect residue info
    if not os.path.exists('resinfo_ref'):
           os.makedirs('resinfo_ref')
    # add column amino acid types
    infile = open("cpptraj_atominfo_%s.txt" % PDB_id_reference, "r")
    outfile = open("./resinfo_ref/cpptraj_resinfo_%s.txt" % PDB_id_reference, "w")
    #outfile.write("site")
    #outfile.write("\t")
    #outfile.write("AAtype")
    #outfile.write("\n")
    infile_lines = infile.readlines()
    for x in range(len(infile_lines)):
        infile_line = infile_lines[x]
        #print(infile_line)
        infile_line_array = re.split("\s+", infile_line)
        if (len(infile_line_array) >= 3):
            site = infile_line_array[1]
            value = infile_line_array[2]
            if (value == "ALA" or value == "ARG" or value == "ASN" or value == "ASP" or value == "CYS" or value == "GLU" or value == "GLN" or value == "GLY" or value == "HIS" or value == "HIE" or value == "HID" or value == "HIP" or value == "ILE" or value == "LEU" or value == "LYS" or value == "MET" or value == "PHE" or value == "PRO" or value == "SER" or value == "THR" or value == "TRP" or value == "TYR" or value == "VAL"):
               #print(site)
               #print(value)
               outfile.write(site)
               outfile.write("\t")
               outfile.write(value)
               outfile.write("\n")
    outfile.close

################################################################################
def feature_vector():
    print("creating feature vector files for machine learning")
    if not os.path.exists('feature_all_query'):
        os.makedirs('feature_all_query')  
    if not os.path.exists('feature_all_ref'):
        os.makedirs('feature_all_ref')
    if not os.path.exists('feature_all_refCTL'):
        os.makedirs('feature_all_refCTL')    
    if not os.path.exists('feature_sub_query'):
        os.makedirs('feature_sub_query')  
    if not os.path.exists('feature_sub_ref'):
        os.makedirs('feature_sub_ref')
    if not os.path.exists('feature_sub_refCTL'):
        os.makedirs('feature_sub_refCTL')    
    if not os.path.exists('feature_all_query_reduced'):
        os.makedirs('feature_all_query_reduced')  
    if not os.path.exists('feature_all_ref_reduced'):
        os.makedirs('feature_all_ref_reduced')
    if not os.path.exists('feature_all_refCTL_reduced'):
        os.makedirs('feature_all_refCTL_reduced')    
    if not os.path.exists('feature_sub_query_reduced'):
        os.makedirs('feature_sub_query_reduced')  
    if not os.path.exists('feature_sub_ref_reduced'):
        os.makedirs('feature_sub_ref_reduced')
    if not os.path.exists('feature_sub_refCTL_reduced'):
        os.makedirs('feature_sub_refCTL_reduced')    
    
    #######################################################
    ###### feature vector for whole reference MD run ######
    #######################################################
    print("creating feature vector for whole MD reference run")
    influx_all_ref = "fluct_%s_all_reference.txt" % PDB_id_reference 
    incorr_all_ref = "corr_%s_all_reference_matrix.txt" % PDB_id_reference    
    dfflux_all_ref = pd.read_csv(influx_all_ref, sep="\s+")
    dfcorr_all_ref = pd.read_csv(incorr_all_ref, sep="\s+", header=None)
    #print(dfflux_all_ref)
    #print(dfcorr_all_ref)
    del dfflux_all_ref[dfflux_all_ref.columns[0]] # remove first column
    # normalize atom fluctuations (minmax method)
    column = 'AtomicFlx'
    dfflux_all_ref[column] = (dfflux_all_ref[column] - dfflux_all_ref[column].min()) / (dfflux_all_ref[column].max() - dfflux_all_ref[column].min())
    #dfflux_all_ref[column] = dfflux_all_ref[column]  # option skip normalization
    # trim uneccessary columns
    #del dfcorr_all_ref[dfcorr_all_ref.columns[0]] # remove first column
    #del dfcorr_all_ref[dfcorr_all_ref.columns[-1]] # remove last column = NaN
    frames_all_ref = [dfflux_all_ref, dfcorr_all_ref]
    feature_all_ref = pd.concat(frames_all_ref, axis = 1, join="inner")
    #print(dfflux_all_ref)
    #print(dfcorr_all_ref)
    #print(feature_all_ref)
    df1 = feature_all_ref
    writePath = "./feature_all_ref/feature_%s_all_ref.txt" % PDB_id_reference
    with open(writePath, 'w') as f1:
        dfAsString = df1.to_string(header=False, index=True)
        f1.write(dfAsString)
    # create reduced atom correlation matrix (from sparse matrix)
    M = pd.DataFrame(dfcorr_all_ref)
    print("Original Matrix:")
    print(M)
    #del M[M[0]]
    #print(M)
    # create sparse matrix
    M[np.abs(M) < 0.005] = 0 # plug in zero values if below threshold
    print("Sparse Matrix:")
    print(M)
    svd =  TruncatedSVD(n_components = 5)
    M_transf = svd.fit_transform(M)
    print("Singular values:")
    print(svd.singular_values_)
    print("Transformed Matrix after reducing to 5 features:")
    print(M_transf)
    M_transf = pd.DataFrame(M_transf)
    print(M_transf) # as dataframe
    # create reduced feature vector
    frames_all_ref_reduced = [dfflux_all_ref, M_transf]
    feature_all_ref_reduced = pd.concat(frames_all_ref_reduced, axis = 1, join="inner")
    df2 = feature_all_ref_reduced
    writePath = "./feature_all_ref_reduced/feature_%s_all_ref.txt" % PDB_id_reference
    with open(writePath, 'w') as f2:
        dfAsString = df2.to_string(header=False, index=True)
        f2.write(dfAsString)
    print("feature vector(whole reference MD run) = atom fluct + 5 reduced atom corr features:")
    print(feature_all_ref_reduced)  
    
    ##############################################################
    ###### feature vectors for subsampled reference MD runs ######
    ##############################################################
    
    for i in range(subsamples):
        print("creating reduced feature vector for subsample %s MD reference run" % i)
        influx_sub_ref = "./atomflux_ref/fluct_%s_sub_reference.txt" % PDB_id_reference 
        incorr_sub_ref = "./atomcorr_ref_matrix/corr_%s_sub_reference_matrix_%s.txt" % (PDB_id_reference, i)    
        dfflux_sub_ref = pd.read_csv(influx_sub_ref, sep="\s+")
        dfcorr_sub_ref = pd.read_csv(incorr_sub_ref, sep="\s+", header=None)
        del dfflux_sub_ref[dfflux_sub_ref.columns[0]] # remove first column
        #del dfflux_sub_ref[dfflux_sub_ref.columns[0]] # remove next column
        # iterate over atom flux columns 
        column = dfflux_sub_ref.columns[i]
        #print(column)
        # normalize atom fluctuations (minmax method)
        dfflux_sub_ref[column] = (dfflux_sub_ref[column] - dfflux_sub_ref[column].min()) / (dfflux_sub_ref[column].max() - dfflux_sub_ref[column].min())
        #dfflux_sub_ref[column] = dfflux_sub_ref[column] # option skip normalization
        myColumn = dfflux_sub_ref[column]
        myColumn = pd.DataFrame(myColumn)
        #print(myColumn)
        #dfflux_sub_ref = dfflux_sub_ref[column]
        # trim uneccessary columns
        del dfcorr_sub_ref[dfcorr_sub_ref.columns[0]] # remove first column
        del dfcorr_sub_ref[dfcorr_sub_ref.columns[-1]] # remove last column = NaN
        #print(dfflux_sub_ref)
        #print(dfcorr_sub_ref)
        frames_sub_ref = [myColumn, dfcorr_sub_ref]
        feature_sub_ref = pd.concat(frames_sub_ref, axis = 1, join="inner")
        #print(dfflux_sub_ref)
        #print(dfcorr_sub_ref)
        #print(feature_sub_ref)
        df1 = feature_sub_ref
        writePath = "./feature_sub_ref/feature_%s_sub_ref_%s.txt" % (PDB_id_reference, i)
        with open(writePath, 'w') as f1:
            dfAsString = df1.to_string(header=False, index=True)
            f1.write(dfAsString)
        # create reduced atom correlation matrix (from sparse matrix)
        M = dfcorr_sub_ref
        #print("Original Matrix:")
        #print(M)
        # create sparse matrix
        M[np.abs(M) < 0.005] = 0 # plug in zero values if below threshold
        #print("Sparse Matrix:")
        #print(M)
        svd =  TruncatedSVD(n_components = 5)
        M_transf = svd.fit_transform(M)
        #print("Singular values:")
        #print(svd.singular_values_)
        #print("Transformed Matrix after reducing to 5 features:")
        #print(M_transf)
        M_transf = pd.DataFrame(M_transf)
        #print(M_transf) # as dataframe
        # create reduced feature vector
        frames_sub_ref_reduced = [myColumn, M_transf]
        feature_sub_ref_reduced = pd.concat(frames_sub_ref_reduced, axis = 1, join="inner")
        df2 = feature_sub_ref_reduced
        writePath = "./feature_sub_ref_reduced/feature_%s_sub_ref_%s.txt" % (PDB_id_reference, i)
        with open(writePath, 'w') as f2:
            dfAsString = df2.to_string(header=False, index=True)
            f2.write(dfAsString)
        #print("feature vector(subsampled reference MD run %s) = atom fluct + 5 reduced atom corr features:" % i)
        #print(feature_sub_ref_reduced) 
    
    #######################################################
    ###### feature vector for whole query MD run ##########
    #######################################################
    print("creating feature vector for whole MD query run")
    influx_all_query = "fluct_%s_all_query.txt" % PDB_id_query 
    incorr_all_query = "corr_%s_all_query_matrix.txt" % PDB_id_query    
    dfflux_all_query = pd.read_csv(influx_all_query, sep="\s+")
    dfcorr_all_query = pd.read_csv(incorr_all_query, sep="\s+", header=None)
    del dfflux_all_query[dfflux_all_query.columns[0]] # remove first column
    # normalize atom fluctuations (minmax method)
    column = 'AtomicFlx'
    dfflux_all_query[column] = (dfflux_all_query[column] - dfflux_all_query[column].min()) / (dfflux_all_query[column].max() - dfflux_all_query[column].min())
    #dfflux_all_query[column] = dfflux_all_query[column] # option skip normalization
    # trim uneccessary columns
    del dfcorr_all_query[dfcorr_all_query.columns[0]] # remove first column
    del dfcorr_all_query[dfcorr_all_query.columns[-1]] # remove last column = NaN
    #print(dfflux_all_query)
    #print(dfcorr_all_query)
    frames_all_query = [dfflux_all_query, dfcorr_all_query]
    feature_all_query = pd.concat(frames_all_query, axis = 1, join="inner")
    #print(dfflux_all_query)
    #print(dfcorr_all_query)
    #print(feature_all_query)
    df1 = feature_all_query
    writePath = "./feature_all_query/feature_%s_all_query.txt" % PDB_id_query
    with open(writePath, 'w') as f1:
        dfAsString = df1.to_string(header=False, index=True)
        f1.write(dfAsString)
    # create reduced atom correlation matrix (from sparse matrix)
    M = dfcorr_all_query
    #print("Original Matrix:")
    #print(M)
    # create sparse matrix
    M[np.abs(M) < 0.005] = 0 # plug in zero values if below threshold
    #print("Sparse Matrix:")
    #print(M)
    svd =  TruncatedSVD(n_components = 5)
    M_transf = svd.fit_transform(M)
    #print("Singular values:")
    #print(svd.singular_values_)
    #print("Transformed Matrix after reducing to 5 features:")
    #print(M_transf)
    M_transf = pd.DataFrame(M_transf)
    #print(M_transf) # as dataframe
    # create reduced feature vector
    frames_all_query_reduced = [dfflux_all_query, M_transf]
    feature_all_query_reduced = pd.concat(frames_all_query_reduced, axis = 1, join="inner")
    df2 = feature_all_query_reduced
    writePath = "./feature_all_query_reduced/feature_%s_all_query.txt" % PDB_id_query
    with open(writePath, 'w') as f2:
        dfAsString = df2.to_string(header=False, index=True)
        f2.write(dfAsString)
    print("feature vector (whole query MD run) = atom fluct + 5 reduced atom corr features:")
    print(feature_all_query_reduced)
        
    ##############################################################
    ###### feature vectors for subsampled query MD runs     ######
    ##############################################################
    
    for i in range(subsamples):
        print("creating reduced feature vector for subsample %s MD query run" % i)
        influx_sub_query = "./atomflux_query/fluct_%s_sub_query.txt" % PDB_id_query 
        incorr_sub_query = "./atomcorr_query_matrix/corr_%s_sub_query_matrix_%s.txt" % (PDB_id_query, i)    
        dfflux_sub_query = pd.read_csv(influx_sub_query, sep="\s+")
        dfcorr_sub_query = pd.read_csv(incorr_sub_query, sep="\s+", header=None)
        del dfflux_sub_query[dfflux_sub_query.columns[0]] # remove first column
        #del dfflux_sub_query[dfflux_sub_query.columns[0]] # remove next column
        # iterate over atom flux columns 
        column = dfflux_sub_query.columns[i]
        #print(column)
        # normalize atom fluctuations (minmax method)
        dfflux_sub_query[column] = (dfflux_sub_query[column] - dfflux_sub_query[column].min()) / (dfflux_sub_query[column].max() - dfflux_sub_query[column].min())
        #dfflux_sub_query[column] = dfflux_sub_query[column] # option skip normalization
        myColumn = dfflux_sub_query[column]
        myColumn = pd.DataFrame(myColumn)
        #print(myColumn)
        #dfflux_sub_query = dfflux_sub_query[column]
        # trim uneccessary columns
        del dfcorr_sub_query[dfcorr_sub_query.columns[0]] # remove first column
        del dfcorr_sub_query[dfcorr_sub_query.columns[-1]] # remove last column = NaN
        #print(dfflux_sub_query)
        #print(dfcorr_sub_query)
        frames_sub_query = [myColumn, dfcorr_sub_query]
        feature_sub_query = pd.concat(frames_sub_query, axis = 1, join="inner")
        #print(dfflux_sub_query)
        #print(dfcorr_sub_query)
        #print(feature_sub_query)
        df1 = feature_sub_query
        writePath = "./feature_sub_query/feature_%s_sub_query_%s.txt" % (PDB_id_query, i)
        with open(writePath, 'w') as f1:
            dfAsString = df1.to_string(header=False, index=True)
            f1.write(dfAsString)
        # create reduced atom correlation matrix (from sparse matrix)
        M = dfcorr_sub_query
        #print("Original Matrix:")
        #print(M)
        # create sparse matrix
        M[np.abs(M) < 0.005] = 0 # plug in zero values if below threshold
        #print("Sparse Matrix:")
        #print(M)
        svd =  TruncatedSVD(n_components = 5)
        M_transf = svd.fit_transform(M)
        #print("Singular values:")
        #print(svd.singular_values_)
        #print("Transformed Matrix after reducing to 5 features:")
        #print(M_transf)
        M_transf = pd.DataFrame(M_transf)
        #print(M_transf) # as dataframe
        # create reduced feature vector
        frames_sub_query_reduced = [myColumn, M_transf]
        feature_sub_query_reduced = pd.concat(frames_sub_query_reduced, axis = 1, join="inner")
        df2 = feature_sub_query_reduced
        writePath = "./feature_sub_query_reduced/feature_%s_sub_query_%s.txt" % (PDB_id_query, i)
        with open(writePath, 'w') as f2:
            dfAsString = df2.to_string(header=False, index=True)
            f2.write(dfAsString)
        #print("feature vector(subsampled reference MD run %s) = atom fluct + 5 reduced atom corr features:" % i)
        #print(feature_sub_ref_reduced) 
    
    ###############################################################
    ###### feature vector for whole reference control MD run ######
    ###############################################################
    print("creating feature vector for whole MD reference control run")
    influx_all_ref = "fluct_%s_all_referenceCTL.txt" % PDB_id_reference 
    incorr_all_ref = "corr_%s_all_referenceCTL_matrix.txt" % PDB_id_reference    
    dfflux_all_ref = pd.read_csv(influx_all_ref, sep="\s+")
    dfcorr_all_ref = pd.read_csv(incorr_all_ref, sep="\s+", header=None)
    #print(dfflux_all_ref)
    #print(dfcorr_all_ref)
    del dfflux_all_ref[dfflux_all_ref.columns[0]] # remove first column
    # normalize atom fluctuations (minmax method)
    column = 'AtomicFlx'
    dfflux_all_ref[column] = (dfflux_all_ref[column] - dfflux_all_ref[column].min()) / (dfflux_all_ref[column].max() - dfflux_all_ref[column].min())
    #dfflux_all_ref[column] = dfflux_all_ref[column]  # option skip normalization
    # trim uneccessary columns
    #del dfcorr_all_ref[dfcorr_all_ref.columns[0]] # remove first column
    #del dfcorr_all_ref[dfcorr_all_ref.columns[-1]] # remove last column = NaN
    frames_all_ref = [dfflux_all_ref, dfcorr_all_ref]
    feature_all_ref = pd.concat(frames_all_ref, axis = 1, join="inner")
    #print(dfflux_all_ref)
    #print(dfcorr_all_ref)
    #print(feature_all_ref)
    df1 = feature_all_ref
    writePath = "./feature_all_refCTL/feature_%s_all_refCTL.txt" % PDB_id_reference
    with open(writePath, 'w') as f1:
        dfAsString = df1.to_string(header=False, index=True)
        f1.write(dfAsString)
    # create reduced atom correlation matrix (from sparse matrix)
    M = pd.DataFrame(dfcorr_all_ref)
    print("Original Matrix:")
    print(M)
    #del M[M[0]]
    #print(M)
    # create sparse matrix
    M[np.abs(M) < 0.005] = 0 # plug in zero values if below threshold
    print("Sparse Matrix:")
    print(M)
    svd =  TruncatedSVD(n_components = 5)
    M_transf = svd.fit_transform(M)
    print("Singular values:")
    print(svd.singular_values_)
    print("Transformed Matrix after reducing to 5 features:")
    print(M_transf)
    M_transf = pd.DataFrame(M_transf)
    print(M_transf) # as dataframe
    # create reduced feature vector
    frames_all_ref_reduced = [dfflux_all_ref, M_transf]
    feature_all_ref_reduced = pd.concat(frames_all_ref_reduced, axis = 1, join="inner")
    df2 = feature_all_ref_reduced
    writePath = "./feature_all_refCTL_reduced/feature_%s_all_refCTL.txt" % PDB_id_reference
    with open(writePath, 'w') as f2:
        dfAsString = df2.to_string(header=False, index=True)
        f2.write(dfAsString)
    print("feature vector(whole reference MD run) = atom fluct + 5 reduced atom corr features:")
    print(feature_all_ref_reduced)  
    
    ##############################################################
    ###### feature vectors for subsampled reference MD runs ######
    ##############################################################
    
    for i in range(subsamples):
        print("creating reduced feature vector for subsample %s MD reference control run" % i)
        influx_sub_ref = "./atomflux_refCTL/fluct_%s_sub_referenceCTL.txt" % PDB_id_reference 
        incorr_sub_ref = "./atomcorr_refCTL_matrix/corr_%s_sub_referenceCTL_matrix_%s.txt" % (PDB_id_reference, i)    
        dfflux_sub_ref = pd.read_csv(influx_sub_ref, sep="\s+")
        dfcorr_sub_ref = pd.read_csv(incorr_sub_ref, sep="\s+", header=None)
        del dfflux_sub_ref[dfflux_sub_ref.columns[0]] # remove first column
        #del dfflux_sub_ref[dfflux_sub_ref.columns[0]] # remove next column
        # iterate over atom flux columns 
        column = dfflux_sub_ref.columns[i]
        #print(column)
        # normalize atom fluctuations (minmax method)
        dfflux_sub_ref[column] = (dfflux_sub_ref[column] - dfflux_sub_ref[column].min()) / (dfflux_sub_ref[column].max() - dfflux_sub_ref[column].min())
        #dfflux_sub_ref[column] = dfflux_sub_ref[column] # option skip normalization
        myColumn = dfflux_sub_ref[column]
        myColumn = pd.DataFrame(myColumn)
        #print(myColumn)
        #dfflux_sub_ref = dfflux_sub_ref[column]
        # trim uneccessary columns
        del dfcorr_sub_ref[dfcorr_sub_ref.columns[0]] # remove first column
        del dfcorr_sub_ref[dfcorr_sub_ref.columns[-1]] # remove last column = NaN
        #print(dfflux_sub_ref)
        #print(dfcorr_sub_ref)
        frames_sub_ref = [myColumn, dfcorr_sub_ref]
        feature_sub_ref = pd.concat(frames_sub_ref, axis = 1, join="inner")
        #print(dfflux_sub_ref)
        #print(dfcorr_sub_ref)
        #print(feature_sub_ref)
        df1 = feature_sub_ref
        writePath = "./feature_sub_refCTL/feature_%s_sub_refCTL_%s.txt" % (PDB_id_reference, i)
        with open(writePath, 'w') as f1:
            dfAsString = df1.to_string(header=False, index=True)
            f1.write(dfAsString)
        # create reduced atom correlation matrix (from sparse matrix)
        M = dfcorr_sub_ref
        #print("Original Matrix:")
        #print(M)
        # create sparse matrix
        M[np.abs(M) < 0.005] = 0 # plug in zero values if below threshold
        #print("Sparse Matrix:")
        #print(M)
        svd =  TruncatedSVD(n_components = 5)
        M_transf = svd.fit_transform(M)
        #print("Singular values:")
        #print(svd.singular_values_)
        #print("Transformed Matrix after reducing to 5 features:")
        #print(M_transf)
        M_transf = pd.DataFrame(M_transf)
        #print(M_transf) # as dataframe
        # create reduced feature vector
        frames_sub_ref_reduced = [myColumn, M_transf]
        feature_sub_ref_reduced = pd.concat(frames_sub_ref_reduced, axis = 1, join="inner")
        df2 = feature_sub_ref_reduced
        writePath = "./feature_sub_refCTL_reduced/feature_%s_sub_refCTL_%s.txt" % (PDB_id_reference, i)
        with open(writePath, 'w') as f2:
            dfAsString = df2.to_string(header=False, index=True)
            f2.write(dfAsString)
        #print("feature vector(subsampled reference MD run %s) = atom fluct + 5 reduced atom corr features:" % i)
        #print(feature_sub_ref_reduced) 
    
    
    
    
#################################################################################
# view movie of entire MD run
def view_reference():
    print("view movie of reference protein")
    #traj = pt.load(PDB_file_reference)
    #view = nv.show_pytraj(traj_file_reference)
    #view.add_representation('licorice', 'water')
    #view.add_representation('cartoon', 'protein')
    #view
def view_query():
    print("view movie of query protein")
    #traj = pt.load(PDB_file_query)
    #view = nv.show_pytraj(traj_file_query)
    #view.add_representation('licorice', 'water')
    #view.add_representation('cartoon', 'protein')
    #view
    
def plot_rmsd():
    print("plotting rmsd to examine stability of the MD simulations")
    # include stat test for stability over time    
    f1 = open("RMSF_%s.ctl" % PDB_id_query, "w")
    f2 = open("RMSF_%s.ctl" % PDB_id_reference, "w")
    f1.write("parm %s\n" % top_file_query)
    f1.write("trajin %s\n" % traj_file_query)
    f1.write("rms out RMSF_%s.txt ToFirst @CA,C,O,N,H&!(:WAT) first\n" % PDB_id_query)
    f1.write("run\n")
    f1.close()
    f2.write("parm %s\n" % top_file_reference)
    f2.write("trajin %s\n" % traj_file_reference)
    f2.write("rms ToFirst @CA,C,O,N,H&!(:WAT) first out RMSF_%s.txt\n" % PDB_id_reference)
    f2.write("run\n")
    f2.close()
    print("calculating RMSF for query protein")
    cmd = 'cpptraj -i RMSF_%s.ctl -o RMSF_%s_out.txt' % (PDB_id_query,PDB_id_query)
    os.system(cmd)
    print("calculating RMSF for reference protein")
    cmd = 'cpptraj -i RMSF_%s.ctl -o RMSF_%s_out.txt' % (PDB_id_reference,PDB_id_reference)
    os.system(cmd)
    inrmsf_query = "RMSF_%s.txt" % PDB_id_query     
    dfrmsf_query = pd.read_csv(inrmsf_query, sep="\s+")
    #print(dfrmsf_query)
    inrmsf_reference = "RMSF_%s.txt" % PDB_id_reference     
    dfrmsf_reference = pd.read_csv(inrmsf_reference, sep="\s+")
    #print(dfrmsf_reference)
    # combine data
    myRMSFframes = (dfrmsf_query, dfrmsf_reference)
    myRMSFindex = pd.concat(myRMSFframes, axis = 1, join="inner")
    myRMSFindex = myRMSFindex.set_axis(['#FrameQ', 'ToFirstQ', '#FrameR', 'ToFirstR'], axis=1, inplace=False)
    print(myRMSFindex)
    #make and save plot
    myRMSFplot = (ggplot() + labs(title='root mean square fluctuation (red is bound or mutated state)', x='frame number', y='RMSF') + geom_line(data = myRMSFindex, mapping = aes(x='#FrameR', y='ToFirstR'), color = 'black') + geom_line(data = myRMSFindex, mapping = aes(x='#FrameQ', y='ToFirstQ'), color = 'red') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    if not os.path.exists('rmsd'):
        os.mkdir('rmsd')
    myRMSFplot.save("rmsd/RMSF_plot.png", width=10, height=5, dpi=300)
    print(myRMSFplot)
    
        
#################################################################################
def compare_dynamics_KL():
    # read total flux files for computing overall diffeerenc
    print("statistical comparison of dynamics via KL divergence metric")
    influx_all_query = "fluct_%s_all_query.txt" % PDB_id_query 
    dfflux_all_query = pd.read_csv(influx_all_query, sep="\s+")
    del dfflux_all_query[dfflux_all_query.columns[0]] # remove first column
    influx_all_ref = "fluct_%s_all_reference.txt" % PDB_id_reference 
    dfflux_all_ref = pd.read_csv(influx_all_ref, sep="\s+")
    del dfflux_all_ref[dfflux_all_ref.columns[0]] # remove first column
    # read subsampled flux files and trim unneeded columns
    influx_sub_query = "./atomflux_query/fluct_%s_sub_query.txt" % PDB_id_query 
    dfflux_sub_query = pd.read_csv(influx_sub_query, sep="\s+")
    del dfflux_sub_query[dfflux_sub_query.columns[0]] # remove first column
    del dfflux_sub_query[dfflux_sub_query.columns[0]] # remove next column
    dfflux_sub_query = dfflux_sub_query.transpose()
    #print(dfflux_sub_query)
    influx_sub_ref = "./atomflux_ref/fluct_%s_sub_reference.txt" % PDB_id_reference 
    dfflux_sub_ref = pd.read_csv(influx_sub_ref, sep="\s+")
    del dfflux_sub_ref[dfflux_sub_ref.columns[0]] # remove first column
    del dfflux_sub_ref[dfflux_sub_ref.columns[0]] # remove next column
    dfflux_sub_ref = dfflux_sub_ref.transpose()
    #print(dfflux_sub_ref)
    
    ##### remove all rows over length of protein chain #####
    rows_to_keep = [x for x in range(length_prot)]
    dfflux_all_query = dfflux_all_query.iloc[rows_to_keep, :]
    dfflux_all_ref = dfflux_all_ref.iloc[rows_to_keep, :]
    columns_to_keep = [x for x in range(length_prot)]
    dfflux_sub_query = dfflux_sub_query.iloc[:, columns_to_keep]
    dfflux_sub_ref = dfflux_sub_ref.iloc[:, columns_to_keep]
        
    ##############################
    ##### calc KL divergence #####
    ##############################
    #myKL = distance.jensenshannon(dfflux_sub_ref, dfflux_sub_query)  # symmetric KL option
    myKL = entropy(dfflux_sub_ref, dfflux_sub_query)  # asymmetric KL option
    #print(myKL)
    myKL = pd.DataFrame(myKL)
    #print(myKL)
    ###########################
    #### 2 sample KS test #####
    ###########################
    myKSlist = []
    myKScolorlist = []
    cutoff = (0.05/(length_prot*0.5)) # multiple test correction
    for d in range(0,length_prot):
        myKS = sp.stats.ks_2samp(dfflux_sub_ref[d], dfflux_sub_query[d], alternative='two-sided')
        #print(myKS)
        myKSlist.append(myKS)
        if(myKS.pvalue < cutoff):
            myKScolor = "sig"
        else:
            myKScolor = "ns"
        myKScolorlist.append(myKScolor)    
    myKSlist = pd.DataFrame(myKSlist)
    myKScolorlist = pd.DataFrame(myKScolorlist)
    #print(myKSlist)
    #print(myKScolorlist)
    myDstat = myKSlist.statistic
    #print(myDstat)
    myPval = myKSlist.pvalue
    #print(myPval)
    
    ###########################
    # sign negative if query flux < ref flux (indicating query binding state)
    diff_flux = dfflux_all_query - dfflux_all_ref
    #print(diff_flux)
    #myKLneg = np.where(myKL>0.09, -myKL, myKL)
    myKLneg = np.where(diff_flux < 0, -myKL, myKL)
    myKLneg = pd.DataFrame(myKLneg)
    #print(myKLneg)
    # index position on protein
    myPOS = [i for i in range(1,length_prot+1)]
    myPOS = pd.DataFrame(myPOS)
    #print(myPOS)
    inres_ref = "./resinfo_ref/cpptraj_resinfo_%s.txt" % PDB_id_reference
    dfres_ref = pd.read_csv(inres_ref, sep="\t", header=None)
    #print(dfres_ref)
    del dfres_ref[dfres_ref.columns[0]] # remove first column
    #print(dfres_ref)
    myRES = dfres_ref
    # collect overall fluctuations for line plots
    dfflux_all_ref = pd.DataFrame(dfflux_all_ref)
    #print(dfflux_all_ref)
    dfflux_all_query = pd.DataFrame(dfflux_all_query)
    #print(dfflux_all_query)
    # rename/add header to columns
    myFrames = (myPOS, myRES, diff_flux, myKLneg, myDstat, myPval, myKScolorlist, dfflux_all_ref, dfflux_all_query)
    myKLindex = pd.concat(myFrames, axis = 1, join="inner")
    myKLindex = myKLindex.set_axis(['pos', 'res', 'dFLUX', 'KL', 'D', 'pvalue', 'p_value', 'FLUX_ref', 'FLUX_query'], axis=1, inplace=False)
    print(myKLindex)
     # write to output file
    if not os.path.exists('divergenceMetrics'):
        os.mkdir('divergenceMetrics')
    df_out = myKLindex
    writePath = "./divergenceMetrics/divergenceMetrics.txt"
    with open(writePath, 'w') as f_out:
        dfAsString = df_out.to_string(header=True, index=False)
        f_out.write(dfAsString)
        f_out.close
    # plot KL divergence and dFLUX
    myplot1 = (ggplot(myKLindex) + aes(x='pos', y='KL', color='res', fill='res') + geom_bar(stat='identity') + labs(title='site-wise signed divergence in atom fluctuation', x='amino acid site', y='signed JS divergence') + theme(panel_background=element_rect(fill='black', alpha=.6)))
    myplot2 = (ggplot(myKLindex) + aes(x='pos', y='dFLUX', color='res', fill='res') + geom_bar(stat='identity') + labs(title='site-wise difference in atom fluctuation', x='amino acid site', y='dFLUX') + theme(panel_background=element_rect(fill='black', alpha=.6)))
    myplot5 = (ggplot(myKLindex) + aes(x='pos', y='D', color='p_value', fill='p_value') + geom_bar(stat='identity') + labs(title='bonferroni corrected significance in divergence in atom fluctuation', x='amino acid site', y='D (2 sample KS test)') + theme(panel_background=element_rect(fill='black', alpha=.6)))
    myplot7 = (ggplot() + labs(title='site-wise atom fluctuation (orange is bound or mutated state)', x='amino acid site', y='atom fluctuation') + geom_line(data = myKLindex, mapping = aes(x='pos', y='FLUX_ref'), color = 'white') + geom_line(data = myKLindex, mapping = aes(x='pos', y='FLUX_query'), color = 'orange') + theme(panel_background=element_rect(fill='black', alpha=.6)))
    myplot3 = (ggplot(myKLindex) + aes(x='pos', y='KL', color='res', fill='res') + geom_bar(stat='identity') + labs(title='site-wise signed divergence in atom fluctuation', x='amino acid site', y='signed JS divergence') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    myplot4 = (ggplot(myKLindex) + aes(x='pos', y='dFLUX', color='res', fill='res') + geom_bar(stat='identity') + labs(title='site-wise difference in atom fluctuation', x='amino acid site', y='dFLUX') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    myplot6 = (ggplot(myKLindex) + aes(x='pos', y='D', color='p_value', fill='p_value') + geom_bar(stat='identity') + labs(title='bonferroni corrected significance in divergence in atom fluctuation', x='amino acid site', y='D (2 sample KS test)') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    myplot8 = (ggplot() + labs(title='site-wise atom fluctuation (red is bound or mutated state)', x='amino acid site', y='atom fluctuation') + geom_line(data = myKLindex, mapping = aes(x='pos', y='FLUX_ref'), color = 'black') + geom_line(data = myKLindex, mapping = aes(x='pos', y='FLUX_query'), color = 'red') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    myplot1.save("divergenceMetrics/KLdivergence_dark.png", width=10, height=5, dpi=300)
    myplot2.save("divergenceMetrics/deltaFLUX_dark.png", width=10, height=5, dpi=300)
    myplot3.save("divergenceMetrics/KLdivergence_light.png", width=10, height=5, dpi=300)
    myplot4.save("divergenceMetrics/deltaFLUX_light.png", width=10, height=5, dpi=300)
    myplot5.save("divergenceMetrics/KStest_dark.png", width=10, height=5, dpi=300)
    myplot6.save("divergenceMetrics/KStest_light.png", width=10, height=5, dpi=300)
    myplot7.save("divergenceMetrics/fluxlines_dark.png", width=10, height=5, dpi=300)
    myplot8.save("divergenceMetrics/fluxlines_light.png", width=10, height=5, dpi=300)
    if(graph_scheme == "light"):
        print(myplot3)
        print(myplot4)
        print(myplot6)
        print(myplot8)
    if(graph_scheme == "dark"):
        print(myplot1)
        print(myplot2)
        print(myplot5)
        print(myplot7)
        
    # candlestickploy
    
   
    # create control, reference PDB and attribute file for chimerax
    os.popen('cp %s.pdb ./ChimeraXvis/query.pdb' % PDB_id_query) # linix
    #os.popen('copy %sREDUCED.pdb ./ChimeraXvis/reference.pdb' % PDB_id_reference) # Windows
    f1 = open("ChimeraXvis_KL.ctl", "w")
    f2 = open("./ChimeraXvis/attributeKL.dat", "w")
    # ctl for KL map
    f1.write("model\t#1\n")
    f1.write("structure\tChimeraXvis/query.pdb\n")
    f1.write("structureADD	ChimeraXvis/reference.pdb\n")
    f1.write("attr_file\tChimeraXvis/attributeKL.dat\n")
    f1.write("length\t%s\n" % length_prot)
    f1.write("attr\tKL\n")
    f1.write("palette\tbluered\n")
    f1.write("lighting\tsimple\n")
    f1.write("transparency\t50\n")
    f1.write("background\tgray\n")
    f2.write("recipient: residues\n")
    f2.write("attribute: KL\n")
    f2.write("\n")
    #print(myKLneg)
    for x in range(length_prot):
        sitepos = x+1
        KLpos = myKLneg.iat[x,0]
        #print(KLpos)
        f2.write("\t:%s\t%s\n" % (sitepos, KLpos))
    
    # create control, reference PDB and attribute file for chimerax
    os.popen('cp %s.pdb ./ChimeraXvis/query.pdb' % PDB_id_query) # linix
    #os.popen('copy %sREDUCED.pdb ./ChimeraXvis/reference.pdb' % PDB_id_reference) # Windows
    f3 = open("ChimeraXvis_KLsig.ctl", "w")
    f4= open("./ChimeraXvis/attributeKLsig.dat", "w")
    # ctl for sig KL map
    f3.write("model\t#1\n")
    f3.write("structure\tChimeraXvis/query.pdb\n")
    f3.write("structureADD	ChimeraXvis/reference.pdb\n")
    f3.write("attr_file\tChimeraXvis/attributeKLsig.dat\n")
    f3.write("length\t%s\n" % length_prot)
    f3.write("attr\tKLsig\n")
    f3.write("palette\tbluered\n")
    f3.write("lighting\tsimple\n")
    f3.write("transparency\t50\n")
    f3.write("background\tgray\n")
    f4.write("recipient: residues\n")
    f4.write("attribute: KLsig\n")
    f4.write("\n")
    #print(myKLneg)
    for x in range(length_prot):
        sitepos = x+1
        #KLpos = myKLneg.iat[x,0]
        KLyn = myKScolorlist.iat[x,0]
        #print(KLyn)
        #print((KLpos))
        if(KLyn == "sig"):
            KLpos = myKLneg.iat[x,0]
        if(KLyn == "ns"):
            KLpos = 0.0
        #print(KLpos)
        f4.write("\t:%s\t%s\n" % (sitepos, KLpos))
    
    
def map_KL():    
    # map KL divergence in chimerax
    print("mapping significant KLdivergence to reference protein %s" % PDB_id_reference)
    cmd = "%sChimeraX color_by_attr_chimerax_KL.py" % chimerax_path
    os.system(cmd)

def map_KLsig():
    # map KL divergence in chimerax
    print("mapping significant KLdivergence to reference protein %s" % PDB_id_reference)
    cmd = "%sChimeraX color_by_attr_chimerax_KLsig.py" % chimerax_path
    os.system(cmd)

def map_MMDsig():
    # map KL divergence in chimerax
    print("mapping significant MMD to reference protein %s" % PDB_id_reference)
    cmd = "%sChimeraX color_by_attr_chimerax_MMDsig.py" % chimerax_path
    os.system(cmd)


def view_KL():    
    # map KL divergence in chimerax
    print("view filtered motions representing dynamic interactions on reference protein %s" % PDB_id_reference)

 
def compare_dynamics_MMD():
    print("statistical comparison of dynamics via max mean discrepancy in learned features")
    # for loop over length of protein
    MMD_output = []
    PVAL_output = []
    for i in range(length_prot-1):
        # initiatize arrays
        feature_reference = []
        feature_referenceCTL = []
        feature_query = []
        for j in range(subsamples):
            samp = j+1
            #print("collecting subsample %s" % samp)
            ######## reference protein ###########
            infeature_reference = "./feature_sub_ref_reduced/feature_%s_sub_ref_%s.txt" % (PDB_id_reference, j)
            df_feature_reference = pd.read_csv(infeature_reference, sep="\s+")
            #print(df_feature_reference)
            del df_feature_reference[df_feature_reference.columns[0]] # remove first column
            #print(df_feature_reference)
            sample_feature_reference = df_feature_reference.iloc[i]
            sample_feature_reference = np.array(sample_feature_reference)
            #print(sample_feature_reference)
            feature_reference.append(sample_feature_reference)
            ######## reference control protein #####
            infeature_referenceCTL = "./feature_sub_refCTL_reduced/feature_%s_sub_refCTL_%s.txt" % (PDB_id_reference, j)
            df_feature_referenceCTL = pd.read_csv(infeature_referenceCTL, sep="\s+")
            #print(df_feature_referenceCTL)
            del df_feature_referenceCTL[df_feature_referenceCTL.columns[0]] # remove first column
            #print(df_feature_referenceCTL)
            sample_feature_referenceCTL = df_feature_referenceCTL.iloc[i]
            sample_feature_referenceCTL = np.array(sample_feature_referenceCTL)
            #print(sample_feature_referenceCTL)
            feature_referenceCTL.append(sample_feature_referenceCTL)
            ######### query protein #########
            infeature_query = "./feature_sub_query_reduced/feature_%s_sub_query_%s.txt" % (PDB_id_query, j)
            df_feature_query = pd.read_csv(infeature_query, sep="\s+")
            #print(df_feature_query)
            del df_feature_query[df_feature_query.columns[0]] # remove first column
            #print(df_feature_query)
            sample_feature_query = df_feature_query.iloc[i]
            sample_feature_query= np.array(sample_feature_query)
            #print(sample_feature_query)
            feature_query.append(sample_feature_query)
            
        print("calculating and bootstrapping MMD for site %s" % i)     
        #print(feature_reference)
        #print(feature_query)
        df_feature_ref = pd.DataFrame(feature_reference)
        df_feature_refCTL = pd.DataFrame(feature_referenceCTL)
        df_feature_query = pd.DataFrame(feature_query)
        feature_ref_mean = df_feature_ref.mean()
        #print(feature_ref_mean)
        feature_query_mean = df_feature_query.mean()
        #print(feature_query_mean)
        # convert back to array for MMD calc
        feature_ref_mean = np.array(feature_ref_mean)
        feature_query_mean = np.array(feature_query_mean)
        feature_ref_mean = feature_ref_mean.reshape(1, -1)
        feature_query_mean = feature_query_mean.reshape(1, -1)
        #print(feature_ref_mean)
        #print(feature_query_mean)
        #myMMD = mmd_rbf(feature_reference, feature_query) # calulate MMD
        myMMD = mmd_rbf(feature_ref_mean, feature_query_mean) # calulate MMD
        #print("obs MMD")
        #print(myMMD)
        MMD_output.append(myMMD) # build MMD list for each site
        
        ##### BOOTSTRAP TEST FOR MMD #########
        cntGREATER = 1
        cntLESSER = 1
        neutralMMDs = []
        for t in range(500):
            # bootstrap1 feature_reference
            rand1 = rnd.randint(0, subsamples-1)
            #print("rand1")
            #print(rand1)
            #print(feature_reference[rand])
            samp1 = feature_reference[rand1]
            samp1 = samp1.reshape(1, -1)
            #print (samp1)
            # bootstrap2 feature_reference control 
            rand2 = rnd.randint(0, subsamples-1)
            #print("rand2")
            #print(rand2)
            samp2 = feature_referenceCTL[rand2]
            samp2 = samp2.reshape(1, -1)
            #print (samp2)
            # neutral MMD (ref1 vs ref2)
            neutralMMD = mmd_rbf(samp1, samp2) # calulate MMD
            #print("neutral MMD %s" % t)
            #print(neutralMMD)
            neutralMMDs.append(neutralMMD)
            # empirical p-value  (freq neutral MMD > alternative MMD)
            if(myMMD > neutralMMD):
                cntGREATER = cntGREATER+1
            if(myMMD <= neutralMMD):
                cntLESSER = cntLESSER+1
        # avg neutral MMD
        mean_neutralMMD = np.mean(neutralMMDs, axis = None)
        #print("avg neutral MMD")
        #print(mean_neutralMMD)
        # empiriacl p value
        emp_P = cntGREATER/(cntGREATER+cntLESSER)
        #print("empirical P value")
        #print(emp_P)
        cutoff = 0.99
        if(emp_P > cutoff):
            p_label = "sig"
        if(emp_P <= cutoff):
            p_label = "ns"
        PVAL_output.append(p_label) # build MMD P VALUE list for each site
    
    # report MMD output array
    MMD_output = pd.DataFrame(MMD_output)
    print(MMD_output)
    # report MMD p value output array
    PVAL_output = pd.DataFrame(PVAL_output)
    print(PVAL_output)
    # index position on protein
    myPOS = [i for i in range(1,length_prot+1)]
    myPOS = pd.DataFrame(myPOS)
    #print(myPOS)
    inres_ref = "./resinfo_ref/cpptraj_resinfo_%s.txt" % PDB_id_reference
    dfres_ref = pd.read_csv(inres_ref, sep="\t", header=None)
    #print(dfres_ref)
    del dfres_ref[dfres_ref.columns[0]] # remove first column
    #print(dfres_ref)
    myRES = dfres_ref
    # rename/add header to columns
    myFrames = (myPOS, myRES, MMD_output, PVAL_output)
    myMMDindex = pd.concat(myFrames, axis = 1, join="inner")
    myMMDindex = myMMDindex.set_axis(['pos', 'res', 'MMD', 'pval'], axis=1, inplace=False)
    print(myMMDindex)
    # write to output file
    if not os.path.exists('maxMeanDiscrepancy'):
        os.mkdir('maxMeanDiscrepancy')
    df_out = myMMDindex
    writePath = "./maxMeanDiscrepancy/maxMeanDiscrepancy.txt"
    with open(writePath, 'w') as f_out:
        dfAsString = df_out.to_string(header=True, index=False)
        f_out.write(dfAsString)
        f_out.close
    # make MMD plots
    myplot9 = (ggplot(myMMDindex) + aes(x='pos', y='MMD', color='pval', fill='pval') + geom_bar(stat='identity') + labs(title='site-wise MMD of learned features between functional states', x='amino acid site', y='MMD') + theme(panel_background=element_rect(fill='black', alpha=.6)))
    myplot10 = (ggplot(myMMDindex) + aes(x='pos', y='MMD', color='pval', fill='pval') + geom_bar(stat='identity') + labs(title='site-wise MMD of learned features between functional states', x='amino acid site', y='MMD') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    myplot11 = (ggplot(myMMDindex) + aes(x='pos', y='MMD', color='res', fill='res') + geom_bar(stat='identity') + labs(title='site-wise MMD of learned features between functional states', x='amino acid site', y='MMD') + theme(panel_background=element_rect(fill='black', alpha=.6)))
    myplot12 = (ggplot(myMMDindex) + aes(x='pos', y='MMD', color='res', fill='res') + geom_bar(stat='identity') + labs(title='site-wise MMD of learned features between functional states', x='amino acid site', y='MMD') + theme(panel_background=element_rect(fill='black', alpha=.1)))
    myplot9.save("maxMeanDiscrepancy/MMD_dark_sig.png", width=10, height=5, dpi=300)
    myplot10.save("maxMeanDiscrepancy/MMD_light_sig.png", width=10, height=5, dpi=300)
    myplot11.save("maxMeanDiscrepancy/MMD_dark_res.png", width=10, height=5, dpi=300)
    myplot12.save("maxMeanDiscrepancy/MMD_light_res.png", width=10, height=5, dpi=300)
    if(graph_scheme == "light"):
        print(myplot10)
        print(myplot12)
    if(graph_scheme == "dark"):
        print(myplot9)
        print(myplot11)
    
    # create control, reference PDB and attribute file for chimerax
    os.popen('cp %s.pdb ./ChimeraXvis/query.pdb' % PDB_id_query) # linix
    #os.popen('copy %sREDUCED.pdb ./ChimeraXvis/reference.pdb' % PDB_id_reference) # Windows
    f5 = open("ChimeraXvis_MMDsig.ctl", "w")
    f6= open("./ChimeraXvis/attributeMMDsig.dat", "w")
    # ctl for sig KL map
    f5.write("model\t#1\n")
    f5.write("structure\tChimeraXvis/query.pdb\n")
    f5.write("structureADD	ChimeraXvis/reference.pdb\n")
    f5.write("attr_file\tChimeraXvis/attributeMMDsig.dat\n")
    f5.write("length\t%s\n" % length_prot)
    f5.write("attr\tMMDsig\n")
    f5.write("palette\tGreens-5\n")
    f5.write("lighting\tsimple\n")
    f5.write("transparency\t50\n")
    f5.write("background\tgray\n")
    f6.write("recipient: residues\n")
    f6.write("attribute: MMDsig\n")
    f6.write("\n")
    #print(myKLneg)
    for x in range(length_prot-1):
        sitepos = x+1
        #MMDpos = MMD_output.iat[x,0]
        MMDyn = PVAL_output.iat[x,0]
        #print(MMDyn)
        #print((MMDpos))
        if(MMDyn == "sig"):
            MMDpos = MMD_output.iat[x,0]
        if(MMDyn == "ns"):
            MMDpos = 0.0
        #print(MMDpos)
        f6.write("\t:%s\t%s\n" % (sitepos, MMDpos))
    
    
    
def mmd_rbf(X, Y, gamma=1.0/6):
    """MMD using rbf (gaussian) kernel (i.e., k(x,y) = exp(-gamma * ||x-y||^2 / 2))
    Arguments:
        X {[n_sample1, dim]} -- [X matrix]
        Y {[n_sample2, dim]} -- [Y matrix]
    Keyword Arguments:
        gamma {float} -- [kernel parameter] (default: {1.0})
    Returns:
        [scalar] -- [MMD value]
    """
    XX = metrics.pairwise.rbf_kernel(X, X, gamma)
    YY = metrics.pairwise.rbf_kernel(Y, Y, gamma)
    XY = metrics.pairwise.rbf_kernel(X, Y, gamma)
    return XX.mean() + YY.mean() - 2 * XY.mean()    
       
def conserved_dynamics():
    print("identifying conserved dynamics")
    
def coordinated_dynamics():
    print("identifying coordinated dynamics")
    myMI = normalized_mutual_info_score([0, 0, 1, 1, 1], [0, 0, 1, 1, 0])
    print(myMI)
def variant_dynamics():
    print("comparing conserved dynamics in genetic and/or drug class variants")
    
###############################################################
###############################################################

def main():
    plot_rmsd()
    feature_vector()  
    #view_query()
    #view_reference()
    if(div_anal == "yes"):
        compare_dynamics_KL()
        map_KL()
        map_KLsig()
        #view_KL()
    if(disc_anal == "yes"):
        compare_dynamics_MMD()
        map_MMDsig()
        
    if(cons_anal == "yes"):
        conserved_dynamics()
    if(coord_anal == "yes"):
        coordinated_dynamics()
    if(var_anal == "yes"):
        variant_dynamics()
    print("comparative analyses of molecular dynamics is completed")
    
    
###############################################################
if __name__ == '__main__':
    main()
    
    