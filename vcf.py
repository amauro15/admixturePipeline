from __future__ import print_function

from popmap import Popmap

import argparse
import os.path
import subprocess
import sys

class VCF():
	'Class for operating on VCF file using VCFtools and Plink'

	def __init__(self, infile, thin, maf, ind, snp, bi):
		self.vcf_file = infile
		self.thin = thin
		self.maf = maf
		self.ind = ind #maximum allowable missing data per snp
		self.snp = snp #maximum allowable missing data per individual
		self.bi = bi #controls biallelic filter

		temp = os.path.splitext(os.path.basename(infile))
		self.prefix = temp[0]

	def run_program(self,string):
		print(string)
		try:
			process = subprocess.Popen(string, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			output, err = process.communicate()
			print(err)
			if process.returncode != 0:
				print("Non-zero exit status:")
				print(process.returncode)
				raise SystemExit
		except (KeyboardInterrupt, SystemExit):
			raise
		except:
			print("Unexpected error:")
			print(sys.exec_info())
			raise SystemExit

	def fix_map(self):
		name = self.prefix + ".map"
		data = self.readfile(name)

		f = open(name,'w')
		for line in data:
			newline = "l" + line.rstrip()
			f.write(newline)
			f.write('\n')
		f.close()

	def convert(self):

		if(self.ind < 1.0 and self.ind > 0.0):
			remove = self.get_ind_coverage()
			#print(remove)

		vcf_command = "vcftools --vcf " + self.vcf_file + " --plink --out " + self.prefix
		if(self.thin > 0):
			vcf_command = vcf_command + " --thin " + str(self.thin)
		if(self.snp < 1.0 and self.snp > 0.0):
			vcf_command = vcf_command + " --max-missing " + str(self.snp)
		if(len(remove) > 0):
			vcf_command = vcf_command + remove
		if(self.maf > 0.0 and self.maf < 1.0):
			vcf_command = vcf_command + " --maf " + str(self.maf)
		if(self.bi == True):
			vcf_command = vcf_command + " --min-alleles 2 --max-alleles 2"
		self.run_program(vcf_command)

		self.fix_map()

	def get_ind_coverage(self):
		vcf_command = "vcftools --vcf " + self.vcf_file + " --missing-indv --out " + self.prefix
		self.run_program(vcf_command)

		fname = self.prefix + ".imiss"
		ret = ""
		with open(fname, 'r') as fh:
			try:
				lnum = 0
				for line in fh:
					line = line.strip()
					if not line:
						continue
					lnum+=1
					if lnum <2: #skip header line
						continue
					else:
						stuff = line.split()
						#print(stuff)
						if float(stuff[4]) > self.ind:
							print("Removing individual %s: %s missing data"%(stuff[0],stuff[4]))
							ret = ret + " --remove-indv " + str(stuff[0])
				return(ret)
			except IOError as e:
				print("Could not read file %s: %s"%(fname,e))
				sys.exit(1)
			except Exception as e:
				print("Unexpected error reading file %s: %s"%(fname,e))
				sys.exit(1)
			finally:
				fh.close()

	def plink(self):
		plink_str_com = "plink --file " + self.prefix + " --allow-extra-chr 0 --recode structure --out " + self.prefix
		self.run_program(plink_str_com)

		plink_command = "plink --file " + self.prefix + " --noweb --allow-extra-chr 0 --recode12 --out " + self.prefix
		#if(self.maf > 0):
		#	maf_float = self.maf/100.0
		#	plink_command = plink_command + " --maf " + str(maf_float)
		self.run_program(plink_command)

	def print_populations(self,popmap):
		data = self.readfile(self.vcf_file)
		popfile = self.prefix + "_pops.txt"
		f = open(popfile,'w')
		for line in data:
			if line.startswith("#CHROM"):
				mylist = line.split()
				del mylist[0:9]
				print(mylist)
				for ind in mylist:
					ind.strip('\t\n\r')
					#print(popmap.get_pop(ind))
					f.write(popmap.get_pop(ind))
					f.write("\n")
		f.close()

	def readfile(self,infile):
		f=open(infile)
		data = f.readlines()
		f.close()
		return data
