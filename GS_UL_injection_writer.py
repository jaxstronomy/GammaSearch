#!/usr/bin/python

# GS_UL_injection_writer - writes injections/searches for verifying analytic upper limits!

from __future__ import division
import sys, getopt, re, os, math, random, subprocess, array, ConfigParser
import numpy as np

def main(argv):

# four sets of 250 injections made: strength 0.9h, 0.95h, 1.05h, 1.10h.

	usage = "GS_UL_injection_writer -c <config file> -r <record file> [--makeSFTs]"

	nInjections = 1
	makeSFTs = False

	try:
		opts, args = getopt.getopt(argv, "hc:r:", ["help", "configFile=","--recordFile=","makeSFTs"])
	except getopt.GetoptError:
		print usage
		sys.exit(2)
	
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print usage
			sys.exit()
		elif opt in ("-c", "--configFile"):
			configfile = arg
		elif opt in ("-r", "--recordFile"):
			recordfile = arg
		elif opt in ("--makeSFTs"):
			makeSFTs = True

	try:
		recordfile
	except:
		sys.stderr.write("Invalid record file " + recordfile)
		sys.exit(1)
	
	searchdata = np.loadtxt(recordfile, skiprows=1)

	try:
		config = ConfigParser.ConfigParser()
		config.read(configfile)
	except:
		sys.stderr.write("Cannot import Config file " + configfile + " exiting...\n")
		sys.exit(1)

	#Variables structure/dictionary

	Vars = {}

	#load inputs/options

	Vars['SearchBand'] = 1
	Vars['Fband'] = 0.1
	Vars['Tau'] = 200
	Vars['m'] = 0.2
	Vars['EphemPath'] = "IAmAnEphemPath"
	Vars['EphemYrs'] = "IAmTheEphemYears"
	Vars['tStartGPS'] = "IAmAStartTime"
	Vars['MFDLogFile'] = "IAmAMFDLogFile"
	Vars['H1MFDInput'] = "IAmH1MFDInput"
	Vars['L1MFDInput'] = "IAmL1MFDInput"
	Vars['CFSInput'] = "IAmTheCFSInput"
	Vars['tObs'] = 5*24*3600
	Vars['EphemEarth'] = "IAmTheEphemEarth"
	Vars['EphemSun'] = "IAmTheEphemSun"
	Vars['2FThresh'] = "IAmThe2FThresh"
	Vars["CFSOutput"] = "IAmTheCFSOutput"
	Vars["CFSHist"] = "IAmCFSHist"
	Vars["CFSTopList"] = "IAmGroot"

	

	#Upper Limit Band FBand
	try:
		Vars['FMin'] = float(config.get("InjVars","ULFMin"))
	except:
		sys.stderr.write("Cannot read FMin\n")
		sys.exit(1)

	#Upper Limit Band Band
	try: 
		Vars['FBand'] = float(config.get("InjVars","ULFBand"))
	except:
		sys.stderr.write("Cannot read FBand\n")
		sys.exit(1)

		
	# will have to have some sort of output file/directory handling here. placeholders for the moment though!

	injectionDag = "IAmAnInjectionDag.dag"
	searchDag = "IAmASearchDag.dag"
	injectionRecord = "IAmAInjectionRecord.dag"
	
	h0_test = (0.9*Vars['h0'], 0.95*Vars['h0'], 1.05*Vars['h0'], 1.10*Vars['h0'])
	TauSecs = Vars['Tau']*365*86400
	

	with open(injectionDag, "w") as MFD:
	
		with open(searchDag, "w") as CFS: 

			with open(injectionRecord, "w") as record:

				for strain in h0_test:

					for i in xrange(0,nInjections):
					
						Vars['h0Test'] = strain

						#generate random nuisance parameters
						Vars['CosIota'] = random.uniform(-1,1)
						Vars['Psi'] = random.uniform(0,2*math.pi)
						Vars['Phi0'] = random.uniform(0,2*math.pi)

						#generate random frequency parameters
						Freq = Vars['FMin'] + Vars['SearchBand']*random.uniform(0,1)
						Vars['FDotMin'] = -Freq/TauSecs
						Vars['FDotMax'] = -Freq/(6.0*TauSecs)
						FDot = Vars['FDotMin'] + (Vars['FDotMax']-Vars['FDotMin'])*random.uniform(0,1)
						Vars['FDotDotMin'] = (2*FDot*FDot)/Freq
						Vars['FDotDotMax'] = (7*FDot*FDot)/Freq
						FDotDot = Vars['FDotDotMin'] + (Vars['FDotDotMax']-Vars['FDotDotMin'])*random.uniform(0,1)
						FreqVars = array.array('d',[0,0,0])
						FreqVars[0] = Freq
						FreqVars[1] = FDot
						FreqVars[2] = FDotDot

						#Calculate search box to generate smaller SFTs
						#Create array with desired tempalte spacings -- [10*df, 6*dfdot, 3*dfdotdot]
						TemplateSpacings = array.array('d',[2*math.sqrt((300*Vars['m'])/((math.pi**2)*(Vars['tObs']**2))),2*math.sqrt((6480*Vars['m'])/((math.pi**2)*(Vars['tObs']**4))),2*math.sqrt((25200*Vars['m'])/((math.pi**2)*(Vars['tObs']**6)))])
						#Use template spacings to create "search box" to search for injections
						SearchBox = array.array('d',[0,0,0])
						SearchBand = array.array('d',[0,0,0])
					  	SearchBox[0] = FreqVars[0] - (4.0 + random.uniform(0,1)) * TemplateSpacings[0]
    						SearchBand[0] = 9 * TemplateSpacings[0]
    						SearchBox[1] = FreqVars[1] - (4.0 + random.uniform(0,1)) * TemplateSpacings[1]
   	 					SearchBand[1] = 9 * TemplateSpacings[1]
    						SearchBox[2] = FreqVars[2] - (4.0 + random.uniform(0,1)) * TemplateSpacings[2]
    						SearchBand[2] = 9 * TemplateSpacings[2]

    						Vars['Padding'] = 0.2

						if (makeSFTs):
    							#Create small-band (UL band) noise SFTs
    							Vars['BandFMin'] = Vars['FMin'] - Vars['SearchBand']
   							Vars['BandFMax'] = Vars['FMin'] + 3*Vars['SearchBand']
    							BandingCmdH1 = 'lalapps_ConvertToSFTv2 --inputSFTs=' + str(Vars['H1InputData']) + ' --outputDir=' + str(Vars['H1MFDInput']) + ' --fmin=' + str(Vars['BandFMin']) + ' --fmax=' + str(Vars['BandFMax'])
    							BandingCmdL1 = 'lalapps_ConvertToSFTv2 --inputSFTs=' + str(Vars['L1InputData']) + ' --outputDir=' + str(Vars['L1MFDInput']) + ' --fmin=' + str(Vars['BandFMin']) + ' --fmax=' + str(Vars['BandFMax']) 
   							print 'Creating small-band SFTs...'
    							print BandingCmdH1
    							subprocess.call(BandingCmdH1, shell=True)
    							print BandingCmdL1
    							subprocess.call(BandingCmdL1, shell=True)
    							print '...done.'
							makeSFTs = False # will only execute the first time through

						#generates MFD and writes out to injection file

						Vars['MFDFmin'] = SearchBox[0] - Vars['Padding']
						Vars['MFDFBand'] = SearchBand[0] + 2*Vars['Padding']
						
						MFDCmdH1 = 'lalapps_Makefakedata_v4 --outSFTbname=' + str(Vars['CFSInput']) + ' --IFO=H1 --ephemDir=' + str(Vars['EphemPath']) + ' --ephemYear=' + str(Vars['EphemYrs']) + ' --fmin=' + str(Vars['MFDFmin']) + ' --Band=' + str(Vars['MFDFBand']) + ' --refTime=' + str(Vars['tStartGPS']) + ' --RA=' + str(Vars['Alpha']) + ' --Dec=' + str(Vars['Delta']) + ' --h0=' + str(Vars['h0Test']) + ' --cosi=' + str(Vars['CosIota']) + ' --psi=' + str(Vars['Psi']) + ' --phi0=' + str(Vars['Phi0']) + ' --Freq=' + str(FreqVars[0]) + ' --f1dot=' + str(FreqVars[1]) + ' --f2dot=' + str(FreqVars[2]) + ' --logfile=' + str(Vars['MFDLogFile']) + ' --noiseSFTs="' + str(Vars['H1MFDInput']) + '/*.sft"'

   						MFDCmdL1 = 'lalapps_Makefakedata_v4 --outSFTbname=' + str(Vars['CFSInput']) + ' --IFO=L1 --ephemDir=' + str(Vars['EphemPath']) + ' --ephemYear=' + str(Vars['EphemYrs']) + ' --fmin=' + str(Vars['MFDFmin']) + ' --Band=' + str(Vars['MFDFBand']) + ' --refTime=' + str(Vars['tStartGPS']) + ' --RA=' + str(Vars['Alpha']) + ' --Dec=' + str(Vars['Delta']) + ' --h0=' + str(Vars['h0Test']) + ' --cosi=' + str(Vars['CosIota']) + ' --psi=' + str(Vars['Psi']) + ' --phi0=' + str(Vars['Phi0']) + ' --Freq=' + str(FreqVars[0]) + ' --f1dot=' + str(FreqVars[1]) + ' --f2dot=' + str(FreqVars[2]) + ' --noiseSFTs="' + str(Vars['L1MFDInput']) + '/*.sft"'
						
						MFD.write(MFDCmdH1 + "\n\n" + MFDCmdL1 + "\n\n")
						
						#generates CFS and writes out to CFS dag

						CFSv2Cmd = 'lalapps_ComputeFStatistic_v2 --RA=' + str(Vars['Alpha']) + ' --Dec=' + str(Vars['Delta']) + ' --Freq=' + str(SearchBox[0]) + ' --f1dot=' + str(SearchBox[1]) + ' --f2dot=' + str(SearchBox[2]) + ' --FreqBand=' + str(SearchBand[0]) + ' --f1dotBand=' + str(SearchBand[1]) + ' --f2dotBand=' + str(SearchBand[2]) + ' --DataFiles="' + str(Vars['CFSInput']) + '/*.sft" --ephemEarth=' + str(Vars['EphemEarth']) + ' --ephemSun=' + str(Vars['EphemSun']) + ' --TwoFthreshold=' + str(Vars['2FThresh']) + ' --outputFstat=' + str(Vars['CFSOutput']) + ' --outputFstatHist=' + str(Vars['CFSHist']) + ' --metricMismatch=' + str(Vars['m']) + ' --gridType=8 --refTime=' + str(Vars['tStartGPS']) + ' --outputSingleFstats=TRUE --outputLoudest=' + str(Vars['CFSTopList']) + ' --useResamp=TRUE'

						CFS.write(CFSv2Cmd + "\n\n")

						record.write(str(Vars) + "\n\n")
						
if __name__ == "__main__":
	main(sys.argv[1:])

