#!/usr/bin/python

#GS_2F_to_UL - collects ComputeFStatistic_v2 outputs and sets up dags to run analytical upper limits. 

from __future__ import division
import sys, getopt, re, os, math

def main(argv):

	usage = "GS_2F_to_UL -s <start frequency> -e <end frequency> -n <source number> -f <file location> [-b <freq band size> -o <output filename> -d <output directory>]"

	#load inputs/options

	startFreq = ''
	endFreq = ''
	fileLocation = '.'
	band = 0.1
	outputDir = '.'
	outFile = False
	
	loudest2F = []

	try:
		opts, args = getopt.getopt(argv, "hs:e:n:f:b:o:d:", ["help", "startFreq=", "endFreq=", "sourceNumber=", "files=", "band=", "outFile=", "outputDir="])
	except getopt.GetoptError:
		print usage
		sys.exit(2)

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			print usage
			sys.exit()
		elif opt in ("-s", "--startFreq"):
			startFreq = float(arg)
		elif opt in ("-e", "--endFreq"):
			endFreq = float(arg)
		elif opt in ("-n", "--sourceNumber"):
			sourceNumber = int(arg)
		elif opt in ("-f", "--files"):
			fileLocation = arg
		elif opt in ("-b", "--band"):
			band = float(arg)
		elif opt in ("-o", "--outFile"):
			outFile = arg
		elif opt in ("-d", "--outputDir"):
			outputDir = arg

	if not(outFile):
		outFile = "GS_UL_" + str(startFreq) + "_" + str(endFreq) + ".dat"

	if not(os.path.isdir(outputDir)):
		os.makedirs(outputDir)

	freqSteps = int(round((endFreq-startFreq)/band))

	with open(outputDir + "/" + outFile, "w") as output:

		with open(outputDir + "/GS_UL_" + str(startFreq) + "_" + str(endFreq) + "_record.dat", "w") as record:

			record.write("f0 Frequency Search RA Dec Fstat\n")

			for step in xrange(0,freqSteps):

				Fstatlist = [] 
				freq = startFreq + step*band
				i = 0
				maxFstat = 0
				maxFstatInd = 0
		
				filename = fileLocation + "/GammaSearch_" + str(freq) + "_" + str(i) + ".dat"
				filepattern = fileLocation + "/Data/GS_" + str(sourceNumber) + "_" + str(freq) + "/*.sft" # need to mod for source no.

				while os.path.isfile(filename):						
					
					with open(filename, 'r') as input:
						data = input.readlines()[20:21]

					for line in data:
						line = line.strip()
						columns = line.split()
						source = {}
						source['freq'] = columns[0]
						source['ra'] = columns[1]
						source['dec'] = columns[2]
						source['Fstat'] = columns[6]
						source['FstatH1'] = columns[7]
						source['FstatL1'] = columns[8]
						source['f0'] = str(freq)
						source['searchno'] = str(i)
						Fstatlist.append(source)
						if (source['Fstat'] > maxFstat):
							maxFstat = source['Fstat']
							maxFstatInd = int(source['searchno'])
			
					i = i + 1
		

					filename = fileLocation + "/GammaSearch_" + str(freq) + "_" + str(i) + ".dat" 
	
	
				if FStatVeto(Fstatlist[maxFstatInd]['Fstat'],Fstatlist[maxFstatInd]['FstatH1'], Fstatlist[maxFstatInd]['FstatL1']):


					record.write(Fstatlist[maxFstatInd]['f0'] + " " + Fstatlist[maxFstatInd]['freq'] + " " + Fstatlist[maxFstatInd]['searchno'] + " " + Fstatlist[maxFstatInd]['ra'] + " " + Fstatlist[maxFstatInd]['dec'] + " " + Fstatlist[maxFstatInd]['Fstat'] + "\n")	

					outputfilename = "UL_" + str(freq) + "_band"
	
					output.write("JOB " + outputfilename + " AnalyticUL.sub\n")
					output.write("RETRY " + outputfilename + " 0\n")
					output.write("VARS " + outputfilename + ' argList=" -a ' + Fstatlist[maxFstatInd]['ra'] + " -d " + Fstatlist[maxFstatInd]['dec'] + " -f " + Fstatlist[maxFstatInd]['f0'] + " -b " + str(band) + " -F " + Fstatlist[maxFstatInd]['Fstat'] + " -D '" + filepattern + "' -E /home/sano/master/opt/lscsoft/lalpulsar/share/lalpulsar -y 09-11 -o " + outputDir + "/" + outputfilename + '.txt"\n')
					output.write("\n")

def FStatVeto(FStat, FStatH1, FStatL1):

	FStat = float(FStat)
	FStatH1 = float(FStatH1)
	FStatL1 = float(FStatL1)

	#vetoing function: consistency check for UL searches.
	#vetos if joint is lower than max of single IFOs or if either single IFO is less than 15

	if (FStat > FStatH1) and (FStat > FStatL1) and (FStatL1 > 15) and (FStatH1 > 15):
		return 1
	else:
		return 0

if __name__ == "__main__":
	main(sys.argv[1:])

	
