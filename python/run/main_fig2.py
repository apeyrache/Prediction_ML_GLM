#!/usr/bin/env python

'''
    File name: main_fig2.py
    Author: Guillaume Viejo
    Date created: 27/03/2017    
    Python Version: 2.7

Fig 2

'''

import warnings
import pandas as pd
import scipy.io
import numpy as np
# Should not import fonctions if already using tensorflow for something else
from fonctions import *
import sys, os
import itertools
import cPickle as pickle


#####################################################################
# DATA LOADING
#####################################################################
adrien_data = scipy.io.loadmat(os.path.expanduser('~/Dropbox (Peyrache Lab)/Peyrache Lab Team Folder/Data/HDCellData/data_test_boosted_tree.mat'))
# m1_imported = scipy.io.loadmat('/home/guillaume/spykesML/data/m1_stevenson_2011.mat')

#####################################################################
# DATA ENGINEERING
#####################################################################
data 			= 	pd.DataFrame()
data['time'] 	= 	np.arange(len(adrien_data['Ang']))		# TODO : import real time from matlab script
data['ang'] 	= 	adrien_data['Ang'].flatten() 			# angular direction of the animal head
data['x'] 		= 	adrien_data['X'].flatten() 				# x position of the animal 
data['y'] 		= 	adrien_data['Y'].flatten() 				# y position of the animal
data['vel'] 	= 	adrien_data['speed'].flatten() 			# velocity of the animal 
# Engineering features
data['cos']		= 	np.cos(adrien_data['Ang'].flatten())	# cosinus of angular direction
data['sin']		= 	np.sin(adrien_data['Ang'].flatten())	# sinus of angular direction
# Firing data
for i in xrange(adrien_data['Pos'].shape[1]): data['Pos'+'.'+str(i)] = adrien_data['Pos'][:,i]
for i in xrange(adrien_data['ADn'].shape[1]): data['ADn'+'.'+str(i)] = adrien_data['ADn'][:,i]



#######################################################################
# FONCTIONS DEFINITIONS
#######################################################################
def extract_tree_threshold(trees):
	n = len(trees.get_dump())
	thr = {}
	for t in xrange(n):
		gv = xgb.to_graphviz(trees, num_trees=t)
		body = gv.body		
		for i in xrange(len(body)):
			for l in body[i].split('"'):
				if 'f' in l and '<' in l:
					tmp = l.split("<")
					if thr.has_key(tmp[0]):
						thr[tmp[0]].append(float(tmp[1]))
					else:
						thr[tmp[0]] = [float(tmp[1])]					
	for k in thr.iterkeys():
		thr[k] = np.sort(np.array(thr[k]))
	return thr

def tuning_curve(x, f, nb_bins):	
	bins = np.linspace(x.min(), x.max()+1e-8, nb_bins+1)
	index = np.digitize(x, bins).flatten()    
	tcurve = np.array([np.mean(f[index == i]) for i in xrange(1, nb_bins+1)])  	
	x = bins[0:-1] + (bins[1]-bins[0])/2.
	return (x, tcurve)

#####################################################################
# COMBINATIONS DEFINITION
#####################################################################
combination = {
	'ang':{
		'ADn':	{
			'features' 	:	['ang'],
			'targets'	:	['ADn.8']
				},
		'Pos':	{
			'features' 	:	['ang'],
			'targets'	:	['Pos.8']
				},		
		},
	'angxy': 	{
		'ADn':		{
			'features' 	:	['ang', 'x', 'y'],
			'targets'	:	['ADn.8']
					},
		'Pos':		{
			'features' 	:	['ang', 'x', 'y'],
			'targets'	:	['Pos.8']
					},				
				}
	}

#####################################################################
# LEARNING XGB Exemples
#####################################################################
params = {'objective': "count:poisson", #for poisson output
    'eval_metric': "logloss", #loglikelihood loss
    'seed': 2925, #for reproducibility
    'silent': 1,
    'learning_rate': 0.05,
    'min_child_weight': 2, 'n_estimators': 580,
    'subsample': 0.6, 'max_depth': 4, 'gamma': 0.0}        
num_round = 150
bsts = {}
for i in combination.iterkeys():
	bsts[i] = {}
	for j in combination[i].iterkeys():
		features = combination[i][j]['features']
		targets = combination[i][j]['targets']	
		X = data[features].values
		Yall = data[targets].values		
		for k in xrange(Yall.shape[1]):
			dtrain = xgb.DMatrix(X, label=Yall[:,k])
			bst = xgb.train(params, dtrain, num_round)
			bsts[i][j] = bst

#####################################################################
# TUNING CURVE
#####################################################################
X = data['ang'].values
example = [combination['ang'][k]['targets'][0] for k in ['ADn', 'Pos']]
tuningc = {}
for k in example:
	Y = data[k].values
	tuningc[k.split(".")[0]] = tuning_curve(X, Y, nb_bins = 60)


#####################################################################
# EXTRACT TREE STRUCTURE
#####################################################################
thresholds = {}
for i in bsts.iterkeys():
	thresholds[i] = {}
	for j in bsts[i].iterkeys():
		thresholds[i][j] = extract_tree_threshold(bsts[i][j])		

########################################################################
# DENSITY PICKLE LOAD
########################################################################

all_data = pickle.load(open("../data/fig2_density.pickle", 'rb'))
angdens = all_data['angdens']
mean_angdens = all_data['mean_angdens']
ratio = all_data['ratio']

########################################################################
# PLOTTING
########################################################################
def figsize(scale):
    fig_width_pt = 483.69687                         # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0/72.27                       # Convert pt to inch
    golden_mean = (np.sqrt(5.0)-1.0)/2.0            # Aesthetic ratio (you could change this)
    fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
    fig_height = fig_width*golden_mean            # height in inches
    fig_size = [fig_width,fig_height]
    return fig_size

def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    # ax.xaxis.set_tick_params(size=6)
    # ax.yaxis.set_tick_params(size=6)


import matplotlib as mpl

mpl.use("pdf")
pdf_with_latex = {                      # setup matplotlib to use latex for output
    "pgf.texsystem": "pdflatex",        # change this if using xetex or lautex
    "text.usetex": True,                # use LaTeX to write all text
    "font.family": "serif",
    "font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
    "font.sans-serif": [],
    "font.monospace": [],
    "axes.labelsize": 5,               # LaTeX default is 10pt font.
    "font.size": 7,
    "legend.fontsize": 5,               # Make the legend/label fonts a little smaller
    "xtick.labelsize": 5,
    "ytick.labelsize": 5,
    "pgf.preamble": [
        r"\usepackage[utf8x]{inputenc}",    # use utf8 fonts becasue your computer can handle it :)
        r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
        ],
    "lines.markeredgewidth" : 0.2,
    "axes.linewidth"        : 0.5,
    "ytick.major.size"      : 1.5,
    "xtick.major.size"      : 1.5
    }    
mpl.rcParams.update(pdf_with_latex)
import matplotlib.gridspec as gridspec
from matplotlib.pyplot import *


order = [['ADn.9', 'ADn.10', 'ADn.11'], ['Pos.8', 'Pos.9', 'Pos.10']]
trans = {'f0':'Angle','f1':'x pos','f2':'y pos'}
colors_ = ['#134B64', '#F5A21E']
title_ = ['Antero-dorsal nucleus', 'Post-subiculum']

figure(figsize = figsize(1))
subplots_adjust(hspace = 0.2, right = 0.999)
# outer = gridspec.GridSpec(2,2, height_ratios = [1, 0.6])
outer = gridspec.GridSpec(2,2)

##PLOT 1#################################################################################################################
# Examples subplot 1 et 2
gs = gridspec.GridSpecFromSubplotSpec(1,2, subplot_spec = outer[0])

for e, i in zip(['ADn','Pos'],range(2)):			
	ax = subplot(gs[i])
	simpleaxis(ax)
	[ax.axvline(l, alpha = 0.1, color = 'grey', linewidth = 0.1) for l in thresholds['ang'][e]['f0']]
	ax.plot(tuningc[e][0], tuningc[e][1], color = colors_[i])
	ax.set_xlim(0, 2*np.pi)
	ax.set_xticks([0, 2*np.pi])
	ax.set_xticklabels(('0', '$2\pi$'))
	ax.set_xlabel('Angle', labelpad = -3.9)
	ax.set_ylabel('f', labelpad = 0.4)		
	ax.locator_params(axis='y', nbins = 3)
	ax.locator_params(axis='x', nbins = 4)
	if j == 0:
		ax.set_title(title_[i], loc = 'right')

##PLOT 2#################################################################################################################
# Centered density
gs = gridspec.GridSpecFromSubplotSpec(1,2, subplot_spec = outer[2])

for g,i in zip(['1.ADn', '1.Pos'], xrange(2)):
	subplot(gs[i])
	subplots_adjust(wspace = 0.5)
	simpleaxis(gca())
	for k in angdens[g].iterkeys():
		plot(angdens[g][k][0], angdens[g][k][1], '-', color = colors_[i], linewidth = 0.4, alpha = 0.5)

	plot(mean_angdens[g][0], mean_angdens[g][1], '-', color = colors_[i], linewidth = 1.2, alpha = 1)	
	# plot(mean_angdens['2.'+g.split('.')[1]][0], mean_angdens['2.'+g.split('.')[1]][1], ':', color = colors_[i], linewidth = 1, alpha = 1)

	ylabel("Density of angular splits")
	# xlabel("Angle (rad)")
	title(title_[i])
	xlim(-np.pi, np.pi)
	xticks([-np.pi, 0, np.pi], ('$-\pi$', '0', '$\pi$'))
	xlabel('Centered', labelpad = 0.4)

##PLOT 4#################################################################################################################
# ang x y density
gs = gridspec.GridSpecFromSubplotSpec(1,2, subplot_spec = outer[3])

subplot(gs[0])
simpleaxis(gca())
x = np.arange(3, dtype = float)
for g, i in zip(ratio.iterkeys(), xrange(2)):
	mean = []
	for k in ratio[g].iterkeys():
		plot(x, ratio[g][k], 'o', alpha = 0.5, color = colors_[i], markersize = 2)
		mean.append(ratio[g][k])
	mean = np.mean(mean, 0)
	bar(x, mean, 0.4, align='center',
        ecolor='k', alpha=.9, color=colors_[i], ec='w')

	x += 0.41
ylabel('Density of splits')

xticks(np.arange(3)+0.205, ('Angle','x pos','y pos'))


# position plot	
	# ax = subplot(gs[j+1])
	# simpleaxis(ax)
	# [ax.axvline(l, alpha = 0.2, color = 'grey', linewidth = 0.1) for l in thresholds[neuron.split(".")[0]][neuron]['f1']]
	# [ax.axhline(l, alpha = 0.2, color = 'grey', linewidth = 0.1) for l in thresholds[neuron.split(".")[0]][neuron]['f2']]	
	# ax.plot(data['x'].values, data['y'].values, '-', color = 'blue', alpha = 0.5, linewidth = 0.2)				
	# ax.set_xlabel('x pos')
	# ax.set_ylabel('y pos')
	# ax.set_xticks([])
	# ax.set_yticks([])	
	# c+=1

# # COunt 
# for i in xrange(2):
# 	gs = gridspec.GridSpecFromSubplotSpec(1,1, subplot_spec = outer[i+2])		
# 	ax = subplot(gs[0])
# 	simpleaxis(ax)
# 	group = order[i][0].split(".")[0]
# 	for neuron in thresholds[group].iterkeys():
# 		count = np.array([len(thresholds[group][neuron][f]) for f in thresholds[group][neuron].iterkeys()])
# 		name = np.array([trans[f] for f in thresholds[group][neuron].keys()])
# 		ax.plot(np.arange(len(count)), count, 'o--', 
# 			color = colors_[i], 
# 			markersize = 1.8, 
# 			linewidth = 0.3,
# 			markerfacecolor = colors_[i],
# 			markeredgecolor = colors_[i],
# 			alpha = 0.6)
# 	for j in xrange(3):
# 		neuron = order[i][j]
# 		count = np.array([len(thresholds[group][neuron][f]) for f in thresholds[group][neuron].keys()])
# 		name = np.array([trans[f] for f in thresholds[neuron.split(".")[0]][neuron].keys()])
# 		ax.plot(np.arange(len(count)), count, 'o-', 
# 			color = colors_[i], 
# 			markersize = 3, 
# 			linewidth = 1.2,
# 			markerfacecolor = colors_[i],
# 			markeredgecolor = colors_[i]
# 			)

	
# 	ax.set_ylabel('Number of split')
# 	ax.set_xticks(np.arange(3))
# 	ax.set_xticklabels(tuple(name))
# 	ax.set_xlabel('Feature')
# 	ax.set_xlim(-0.2, 2.2)
# 	ax.locator_params(axis='y', nbins = 3)


savefig("../../figures/fig2.pdf", dpi = 900, bbox_inches = 'tight', facecolor = 'white')
os.system("evince ../../figures/fig2.pdf &")


